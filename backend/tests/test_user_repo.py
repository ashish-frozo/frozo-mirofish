"""Tests for UserRepository."""

import pytest
from app.repositories.user_repo import UserRepository


class TestUserRepository:
    def test_create_user(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(email="test@example.com", name="Test User", password="securepass123")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.password_hash is not None
        assert user.password_hash != "securepass123"
        assert user.plan == "trial"

    def test_get_by_email(self, db_session):
        repo = UserRepository(db_session)
        repo.create(email="find@example.com", name="Find Me", password="pass123")
        user = repo.get_by_email("find@example.com")
        assert user is not None
        assert user.name == "Find Me"

    def test_get_by_email_not_found(self, db_session):
        repo = UserRepository(db_session)
        user = repo.get_by_email("nonexistent@example.com")
        assert user is None

    def test_verify_password(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(email="verify@example.com", name="Verify", password="mypassword")
        assert repo.verify_password(user, "mypassword") is True
        assert repo.verify_password(user, "wrongpassword") is False

    def test_create_or_update_google_user_new(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create_or_update_google_user(
            google_id="google123",
            email="oauth@example.com",
            name="OAuth User",
            avatar_url="https://example.com/avatar.jpg"
        )
        assert user.google_id == "google123"
        assert user.auth_provider == "google"
        assert user.password_hash is None

    def test_create_or_update_google_user_existing(self, db_session):
        repo = UserRepository(db_session)
        user1 = repo.create_or_update_google_user(
            google_id="g456", email="existing@example.com", name="First"
        )
        user2 = repo.create_or_update_google_user(
            google_id="g456", email="existing@example.com", name="Updated Name"
        )
        assert user1.id == user2.id
        assert user2.name == "Updated Name"

    def test_is_trial_expired_active(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(email="trial@example.com", name="Trial", password="pass")
        assert repo.is_trial_expired(user) is False

    def test_is_trial_expired_paid(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(email="paid@example.com", name="Paid", password="pass")
        user.plan = "pro"
        assert repo.is_trial_expired(user) is False

    def test_get_by_id(self, db_session):
        repo = UserRepository(db_session)
        created = repo.create(email="byid@example.com", name="ById", password="pass")
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.email == "byid@example.com"

    def test_soft_delete_hidden(self, db_session):
        repo = UserRepository(db_session)
        from datetime import datetime, timezone
        user = repo.create(email="deleted@example.com", name="Deleted", password="pass")
        user.deleted_at = datetime.now(timezone.utc)
        db_session.flush()
        found = repo.get_by_email("deleted@example.com")
        assert found is None
