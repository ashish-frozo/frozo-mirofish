"""Centralized error handling."""

import traceback
from flask import jsonify
from ..utils.logger import get_logger

logger = get_logger('mirofish.errors')


class AuthError(Exception):
    pass

class ForbiddenError(Exception):
    pass

class NotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass


def register_error_handlers(app):
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(AuthError)
    def handle_auth_error(e):
        return jsonify({"error": str(e), "code": "AUTH_ERROR"}), 401

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(e):
        return jsonify({"error": str(e), "code": "FORBIDDEN"}), 403

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": str(e), "code": "NOT_FOUND"}), 404

    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422

    @app.errorhandler(Exception)
    def handle_generic(e):
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        payload = {"error": "Internal server error", "code": "INTERNAL_ERROR"}
        if app.debug:
            payload["traceback"] = traceback.format_exc()
        return jsonify(payload), 500
