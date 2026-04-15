"""
LLM client wrapper
Unified OpenAI-compatible API calls
"""

import json
import re
import threading
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
from .logger import get_logger

_cost_logger = get_logger('mirofish.llm.cost')

# Approximate prices in USD per 1M tokens (input, output). OpenRouter-style slugs.
# Unknown models fall back to (0, 0) — tokens still logged, cost shown as "n/a".
# Update as pricing changes; this is a rough running estimate, not an invoice.
_PRICE_TABLE: Dict[str, tuple] = {
    # Anthropic
    "anthropic/claude-haiku-4-5": (1.00, 5.00),
    "anthropic/claude-sonnet-4-5": (3.00, 15.00),
    "anthropic/claude-opus-4-5": (15.00, 75.00),
    # Google
    "google/gemini-2.0-flash-001": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.30, 2.50),
    # DeepSeek
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek/deepseek-chat-v3": (0.14, 0.28),
    # OpenAI
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    # Meta
    "meta-llama/llama-3.3-70b-instruct": (0.13, 0.40),
}

# Process-wide running totals. Thread-safe, reset on process restart.
_TOTALS_LOCK = threading.Lock()
_TOTALS = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "calls": 0}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_price, out_price = _PRICE_TABLE.get(model, (0.0, 0.0))
    return (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000


def get_cost_totals() -> Dict[str, Any]:
    """Return a copy of the running LLM spend totals since process start."""
    with _TOTALS_LOCK:
        return dict(_TOTALS)


def _current_task_id() -> Optional[str]:
    """Return the task_id that owns the currently running LLM call, if any.

    Resolved from (in order):
      1. ``MIROFISH_COST_TASK_ID`` env var — set by the parent process on
         ``subprocess.Popen`` so camel-oasis simulations attribute back to
         their prediction.
      2. Nothing — the call is untracked per-task but still rolls into the
         process-wide totals.

    Env var is used rather than a thread-local because it must propagate
    into subprocesses and into thread-pool workers spun by camel-oasis.
    The accepted trade-off is that two overlapping predictions in the same
    Flask process will cross-attribute any Flask-side LLM calls made
    between the start of one and the end of the other.
    """
    import os as _os
    v = _os.environ.get("MIROFISH_COST_TASK_ID")
    return v if v else None


def record_usage(response: Any, model: str) -> None:
    """Log token/cost from a raw OpenAI-SDK response and roll into running totals.

    Idempotent: tags the response with ``_mirofish_tracked`` on first call so
    the monkey-patch in :func:`install_openai_cost_tracker` and any explicit
    call sites can coexist without double-counting. Also bumps the per-task
    Redis counters for whichever task_id is currently active, so admins can
    see cost-per-prediction.
    """
    try:
        if getattr(response, "_mirofish_tracked", False):
            return
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        pt = int(getattr(usage, "prompt_tokens", 0) or 0)
        ct = int(getattr(usage, "completion_tokens", 0) or 0)
        cost = _estimate_cost(model, pt, ct)
        cost_str = f"${cost:.6f}" if model in _PRICE_TABLE else "n/a"
        with _TOTALS_LOCK:
            _TOTALS["prompt_tokens"] += pt
            _TOTALS["completion_tokens"] += ct
            _TOTALS["cost_usd"] += cost
            _TOTALS["calls"] += 1
            running = dict(_TOTALS)
        _cost_logger.info(
            "llm_call model=%s in=%d out=%d cost=%s | run_totals calls=%d in=%d out=%d cost=$%.4f",
            model, pt, ct, cost_str,
            running["calls"], running["prompt_tokens"],
            running["completion_tokens"], running["cost_usd"],
        )

        # Per-task attribution. Imported inline to keep llm_client importable
        # from contexts (scripts, tests) that don't bring the full service layer.
        task_id = _current_task_id()
        if task_id:
            try:
                from ..services.cost_tracker import bump as _bump_task
                _bump_task(task_id, pt, ct, cost)
            except Exception as e:
                _cost_logger.debug("per-task cost attribution skipped: %s", e)

        try:
            setattr(response, "_mirofish_tracked", True)
        except Exception:
            pass
    except Exception as e:
        _cost_logger.debug("cost accounting skipped: %s", e)


_PATCH_INSTALLED = False


def install_openai_cost_tracker() -> None:
    """Monkey-patch openai SDK so every chat.completions.create is tracked.

    Covers all callers in the current process — including third-party libraries
    like camel-oasis that spin up their own OpenAI clients. Call once at process
    startup (Flask ``create_app`` for the API, and the top of each standalone
    simulation script). Safe to call multiple times; re-installs are no-ops.

    Streaming responses return an iterator rather than a ChatCompletion and
    therefore carry no usage block — those are silently skipped.
    """
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return
    try:
        from openai.resources.chat import completions as _sync_mod
        from openai.resources.chat import completions as _async_mod  # noqa: F401
        SyncCompletions = _sync_mod.Completions
        AsyncCompletions = _sync_mod.AsyncCompletions

        _orig_sync_create = SyncCompletions.create
        _orig_async_create = AsyncCompletions.create

        def _tracked_sync_create(self, *args, **kwargs):
            resp = _orig_sync_create(self, *args, **kwargs)
            try:
                model = kwargs.get("model") or getattr(resp, "model", "unknown")
                record_usage(resp, model)
            except Exception:
                pass
            return resp

        async def _tracked_async_create(self, *args, **kwargs):
            resp = await _orig_async_create(self, *args, **kwargs)
            try:
                model = kwargs.get("model") or getattr(resp, "model", "unknown")
                record_usage(resp, model)
            except Exception:
                pass
            return resp

        SyncCompletions.create = _tracked_sync_create
        AsyncCompletions.create = _tracked_async_create
        _PATCH_INSTALLED = True
        _cost_logger.info("openai cost tracker installed")
    except Exception as e:
        _cost_logger.warning("failed to install openai cost tracker: %s", e)


class LLMClient:
    """LLM client"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request.

        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens
            response_format: Response format (e.g., JSON mode)

        Returns:
            Model response text
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        record_usage(response, self.model)
        content = response.choices[0].message.content
        # Some models (e.g., MiniMax M2.5) may include <think> reasoning content that needs to be removed
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request and return JSON.

        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens

        Returns:
            Parsed JSON object
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Clean up markdown code block markers
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON returned by LLM: {cleaned_response}")
