"""Auth API blueprint — signup, login, refresh, logout, me."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, g
from jose import jwt

from ..config import Config
from ..db import get_db
from ..middleware.auth import require_auth
from ..models.db_models import RefreshTokenModel
from ..repositories.user_repo import UserRepository

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _generate_tokens(session, user):
    """Generate access + refresh tokens. Stores refresh token hash in DB."""
    access_token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        },
        Config.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    refresh_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    rt = RefreshTokenModel(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES),
    )
    session.add(rt)
    session.flush()

    return access_token, refresh_token


def _user_dict(user):
    """Serialize a UserModel to a JSON-safe dict."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "plan": user.plan,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """User signup
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name:
              type: string
              example: Jane Doe
            email:
              type: string
              example: jane@example.com
            password:
              type: string
              example: securepass123
    responses:
      201:
        description: Signup successful
        schema:
          type: object
          properties:
            access_token: {type: string}
            refresh_token: {type: string}
            user:
              type: object
              properties:
                id: {type: string}
                email: {type: string}
                name: {type: string}
      409:
        description: Email already registered
      422:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    # Validation
    errors = []
    if not email or not _EMAIL_RE.match(email):
        errors.append("Valid email is required")
    if not name:
        errors.append("Name is required")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if errors:
        return jsonify({"error": "; ".join(errors), "code": "VALIDATION_ERROR"}), 422

    with get_db() as session:
        repo = UserRepository(session)

        if repo.get_by_email(email):
            return jsonify({"error": "Email already registered", "code": "DUPLICATE_EMAIL"}), 409

        user = repo.create(email, name, password)
        access_token, refresh_token = _generate_tokens(session, user)

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": _user_dict(user),
        }), 201


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    """User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: mypassword123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success: {type: boolean}
            access_token: {type: string}
            refresh_token: {type: string}
      401:
        description: Invalid credentials
      422:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required", "code": "VALIDATION_ERROR"}), 422

    with get_db() as session:
        repo = UserRepository(session)
        user = repo.get_by_email(email)

        if not user or not repo.verify_password(user, password):
            return jsonify({"error": "Invalid email or password", "code": "INVALID_CREDENTIALS"}), 401

        access_token, refresh_token = _generate_tokens(session, user)

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": _user_dict(user),
        }), 200


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh access token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [refresh_token]
          properties:
            refresh_token:
              type: string
              description: Refresh token from login or previous refresh
    responses:
      200:
        description: Token refreshed
        schema:
          type: object
          properties:
            access_token: {type: string}
            refresh_token: {type: string}
      401:
        description: Invalid or expired refresh token
      422:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    raw_token = data.get("refresh_token") or ""

    if not raw_token:
        return jsonify({"error": "Refresh token is required", "code": "VALIDATION_ERROR"}), 422

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    with get_db() as session:
        rt = (
            session.query(RefreshTokenModel)
            .filter(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .first()
        )

        if not rt or rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return jsonify({"error": "Invalid or expired refresh token", "code": "INVALID_TOKEN"}), 401

        # Revoke old token
        rt.revoked_at = datetime.now(timezone.utc)

        # Load user
        repo = UserRepository(session)
        user = repo.get_by_id(rt.user_id)
        if not user:
            return jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 401

        # Generate new pair
        access_token, new_refresh_token = _generate_tokens(session, user)

        return jsonify({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }), 200


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """User logout
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            refresh_token:
              type: string
              description: Refresh token to revoke
    responses:
      200:
        description: Logged out successfully
        schema:
          type: object
          properties:
            message: {type: string}
    """
    data = request.get_json(silent=True) or {}
    raw_token = data.get("refresh_token") or ""

    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        session = g.db_session
        rt = (
            session.query(RefreshTokenModel)
            .filter(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .first()
        )
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            session.flush()

    return jsonify({"message": "Logged out"}), 200


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    """Get current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user info
        schema:
          type: object
          properties:
            user:
              type: object
              properties:
                id: {type: string}
                email: {type: string}
                name: {type: string}
                avatar_url: {type: string}
                plan: {type: string}
                created_at: {type: string}
      401:
        description: Not authenticated
    """
    user = g.current_user
    return jsonify({"user": _user_dict(user)}), 200


# ---------------------------------------------------------------------------
# PUT /api/auth/me
# ---------------------------------------------------------------------------

@auth_bp.route("/me", methods=["PUT"])
@require_auth
def update_me():
    """Update current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: New Name
            avatar_url:
              type: string
              example: https://example.com/avatar.png
    responses:
      200:
        description: User updated
        schema:
          type: object
          properties:
            user:
              type: object
              properties:
                id: {type: string}
                email: {type: string}
                name: {type: string}
      401:
        description: Not authenticated
      422:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    user = g.current_user
    session = g.db_session

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "Name cannot be empty", "code": "VALIDATION_ERROR"}), 422
        user.name = name

    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    session.flush()
    return jsonify({"user": _user_dict(user)}), 200
