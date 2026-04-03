"""Tests for Redis cache service."""
from unittest.mock import patch


def test_cache_get_set():
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get, cache_set
        cache_set("test_key", {"foo": "bar"}, ttl=60)
        result = cache_get("test_key")
        assert result == {"foo": "bar"}


def test_cache_miss_returns_none():
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get
        result = cache_get("nonexistent")
        assert result is None


def test_cache_invalidate():
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get, cache_set, cache_invalidate
        cache_set("to_delete", "value", ttl=60)
        cache_invalidate("to_delete")
        assert cache_get("to_delete") is None


def test_cache_unavailable_returns_none():
    with patch('app.services.cache_service.get_redis', return_value=None):
        from app.services.cache_service import cache_get, cache_set
        cache_set("key", "val")
        assert cache_get("key") is None
