"""Service-to-service authentication middleware for BettaFish integration."""
import functools
from flask import request, jsonify, g
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.service_auth')


def service_auth_required(f):
    """Decorator: require valid service API key in X-Service-Key header.

    Sets g.service_origin = 'bettafish' on success.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        service_key = request.headers.get('X-Service-Key', '')

        if not Config.BETTAFISH_SERVICE_KEY:
            logger.error("BETTAFISH_SERVICE_KEY not configured")
            return jsonify({"success": False, "error": "Service integration not configured"}), 503

        if not service_key or service_key != Config.BETTAFISH_SERVICE_KEY:
            logger.warning("Invalid service key attempt")
            return jsonify({"success": False, "error": "Invalid service key"}), 401

        g.service_origin = 'bettafish'
        return f(*args, **kwargs)

    return decorated
