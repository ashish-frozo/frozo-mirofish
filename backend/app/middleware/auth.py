"""Authentication middleware."""

import functools
import uuid as _uuid
from datetime import datetime, timezone

from flask import request, g, jsonify
from jose import jwt, JWTError

from ..config import Config
from ..db import get_db
from ..repositories.user_repo import UserRepository


def _get_token_from_request():
    """Extract JWT from Authorization header or cookie."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("access_token")


def require_auth(f):
    """Decorator: require valid JWT. Sets g.current_user and g.db_session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token_from_request()
        if not token:
            return jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}), 401

        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            return jsonify({"error": "Invalid or expired token", "code": "INVALID_TOKEN"}), 401

        user_id_str = payload.get("sub")
        if not user_id_str:
            return jsonify({"error": "Invalid token payload", "code": "INVALID_TOKEN"}), 401

        try:
            user_id = _uuid.UUID(user_id_str)
        except (ValueError, AttributeError):
            return jsonify({"error": "Invalid token payload", "code": "INVALID_TOKEN"}), 401

        with get_db() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                return jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 401

            g.current_user = user
            g.db_session = session
            return f(*args, **kwargs)

    return decorated


def require_active_plan(f):
    """Decorator: require non-expired trial or active paid plan. Must be used after @require_auth."""
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        user = g.current_user
        if user.plan == "trial" and datetime.now(timezone.utc) > user.trial_ends_at:
            return jsonify({
                "error": "Trial expired",
                "code": "TRIAL_EXPIRED",
                "trial_ends_at": user.trial_ends_at.isoformat(),
            }), 403
        return f(*args, **kwargs)

    return decorated
