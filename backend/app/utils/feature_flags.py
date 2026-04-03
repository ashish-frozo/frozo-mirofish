"""Simple file + env var feature flag system."""

import os
import json
from ..utils.logger import get_logger

logger = get_logger('mirofish.feature_flags')

_flags = {}
_loaded = False


def _load_flags():
    """Load flags from JSON file (once)."""
    global _flags, _loaded
    if _loaded:
        return
    flags_path = os.path.join(os.path.dirname(__file__), '../../../feature_flags.json')
    try:
        with open(flags_path, 'r') as f:
            _flags = json.load(f)
        logger.info(f"Loaded {len(_flags)} feature flags")
    except FileNotFoundError:
        logger.warning("feature_flags.json not found, using empty defaults")
        _flags = {}
    _loaded = True


def is_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.
    Env var FF_<FLAG_NAME> takes precedence over JSON file.
    """
    env_key = f"FF_{flag_name.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        return env_val.lower() in ('true', '1', 'yes')

    _load_flags()
    val = _flags.get(flag_name)
    if isinstance(val, bool):
        return val
    return bool(val)


def get_value(flag_name: str):
    """
    Get a feature flag value (any type).
    Env var FF_<FLAG_NAME> takes precedence.
    """
    env_key = f"FF_{flag_name.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        try:
            return json.loads(env_val)
        except (json.JSONDecodeError, ValueError):
            return env_val

    _load_flags()
    return _flags.get(flag_name)
