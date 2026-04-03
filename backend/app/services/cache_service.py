"""Redis caching service with decorator support."""

import json
import functools
import hashlib
from typing import Optional, Any

import redis

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.cache')

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis connection. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.from_url(
            Config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        _redis_client = None
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(f"cache:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.debug(f"Cache get error for {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL in seconds."""
    r = get_redis()
    if not r:
        return
    try:
        r.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug(f"Cache set error for {key}: {e}")


def cache_invalidate(key: str) -> None:
    """Delete a specific cache key."""
    r = get_redis()
    if not r:
        return
    try:
        r.delete(f"cache:{key}")
    except Exception:
        pass


def cache_invalidate_pattern(pattern: str) -> None:
    """Delete all cache keys matching a pattern."""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(f"cache:{pattern}")
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def cached(key_template: str, ttl: int = 300):
    """
    Decorator for caching function results.

    Usage:
        @cached("entities:{graph_id}", ttl=600)
        def get_entities(graph_id):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            try:
                cache_key = key_template.format(**bound.arguments)
            except KeyError:
                return func(*args, **kwargs)

            result = cache_get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
