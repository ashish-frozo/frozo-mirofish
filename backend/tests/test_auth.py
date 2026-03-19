"""Tests for the auth API blueprint."""

import json
import pytest


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        resp = client.post("/api/auth/signup", json={
            "email": "alice@example.com",
            "name": "Alice",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["name"] == "Alice"
        assert data["user"]["plan"] == "trial"
        assert data["user"]["id"]

    def test_signup_duplicate_email(self, client):
        client.post("/api/auth/signup", json={
            "email": "dup@example.com",
            "name": "First",
            "password": "securepass123",
        })
        resp = client.post("/api/auth/signup", json={
            "email": "dup@example.com",
            "name": "Second",
            "password": "securepass456",
        })
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "DUPLICATE_EMAIL"

    def test_signup_short_password(self, client):
        resp = client.post("/api/auth/signup", json={
            "email": "short@example.com",
            "name": "Short",
            "password": "abc",
        })
        assert resp.status_code == 422
        assert "VALIDATION_ERROR" in resp.get_json()["code"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def _create_user(self, client, email="login@example.com", password="securepass123"):
        client.post("/api/auth/signup", json={
            "email": email,
            "name": "Tester",
            "password": password,
        })

    def test_login_success(self, client):
        self._create_user(client)
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self, client):
        self._create_user(client, email="wrongpw@example.com")
        resp = client.post("/api/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert resp.get_json()["code"] == "INVALID_CREDENTIALS"

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nouser@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 401
        assert resp.get_json()["code"] == "INVALID_CREDENTIALS"


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

class TestMe:
    def _signup_and_get_token(self, client, email="me@example.com"):
        resp = client.post("/api/auth/signup", json={
            "email": email,
            "name": "Me User",
            "password": "securepass123",
        })
        return resp.get_json()["access_token"]

    def test_me_authenticated(self, client):
        token = self._signup_and_get_token(client)
        resp = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["email"] == "me@example.com"
        assert data["user"]["name"] == "Me User"
        assert "created_at" in data["user"]

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def _signup_and_get_tokens(self, client, email="refresh@example.com"):
        resp = client.post("/api/auth/signup", json={
            "email": email,
            "name": "Refresher",
            "password": "securepass123",
        })
        data = resp.get_json()
        return data["access_token"], data["refresh_token"]

    def test_refresh_success(self, client):
        access_token, refresh_token = self._signup_and_get_tokens(client)
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client):
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-token-value",
        })
        assert resp.status_code == 401

    def test_refresh_reuse_revoked_token(self, client):
        _, refresh_token = self._signup_and_get_tokens(client, email="reuse@example.com")
        # First refresh — should succeed and revoke original
        resp1 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp1.status_code == 200
        # Second refresh with same token — should fail (already revoked)
        resp2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout(self, client):
        # Signup
        resp = client.post("/api/auth/signup", json={
            "email": "logout@example.com",
            "name": "LogoutUser",
            "password": "securepass123",
        })
        data = resp.get_json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Logout
        resp = client.post("/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200

        # Refresh with revoked token should fail
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 401
