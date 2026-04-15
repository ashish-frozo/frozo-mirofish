"""Per-task LLM cost counters.

Persists running totals in Redis so the Flask process and its spawned
simulation subprocesses share a single view of a prediction's spend.
Survives restarts as long as Redis is up; falls back to a no-op when
Redis is unavailable so cost tracking is never in the critical path.

Key layout:
    cost:task:{task_id}  -> hash { prompt_tokens, completion_tokens, calls, cost_usd_micro }

``cost_usd_micro`` stores USD * 1_000_000 as an integer so Redis HINCRBY
stays atomic — we convert back to float on read.
"""

from typing import Dict, Optional

from .cache_service import get_redis
from ..utils.logger import get_logger

logger = get_logger('mirofish.cost_tracker')

_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days; cost rows are also persisted to DB at completion


def _key(task_id: str) -> str:
    return f"cost:task:{task_id}"


def bump(task_id: str, prompt_tokens: int, completion_tokens: int, cost_usd: float) -> None:
    """Atomically add a single LLM call's spend to this task's counters."""
    if not task_id:
        return
    r = get_redis()
    if not r:
        return
    try:
        pipe = r.pipeline()
        k = _key(task_id)
        pipe.hincrby(k, "prompt_tokens", int(prompt_tokens))
        pipe.hincrby(k, "completion_tokens", int(completion_tokens))
        pipe.hincrby(k, "calls", 1)
        pipe.hincrby(k, "cost_usd_micro", int(round(cost_usd * 1_000_000)))
        pipe.expire(k, _TTL_SECONDS)
        pipe.execute()
    except Exception as e:
        logger.debug(f"cost_tracker.bump failed for {task_id}: {e}")


def get(task_id: str) -> Dict[str, float]:
    """Snapshot the current totals for a task. Missing fields default to 0."""
    empty = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "cost_usd": 0.0}
    if not task_id:
        return empty
    r = get_redis()
    if not r:
        return empty
    try:
        raw = r.hgetall(_key(task_id))
        if not raw:
            return empty
        return {
            "prompt_tokens": int(raw.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(raw.get("completion_tokens", 0) or 0),
            "calls": int(raw.get("calls", 0) or 0),
            "cost_usd": int(raw.get("cost_usd_micro", 0) or 0) / 1_000_000,
        }
    except Exception as e:
        logger.debug(f"cost_tracker.get failed for {task_id}: {e}")
        return empty


def clear(task_id: str) -> None:
    """Delete the counters after they have been persisted to the task row."""
    if not task_id:
        return
    r = get_redis()
    if not r:
        return
    try:
        r.delete(_key(task_id))
    except Exception:
        pass
