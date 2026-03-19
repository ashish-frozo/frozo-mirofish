"""User repository — handles all user-related database operations."""

import uuid as _uuid
from datetime import datetime, timedelta, timezone
import bcrypt
from sqlalchemy.orm import Session

from ..models.db_models import UserModel


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds. Returns a str."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, email: str, name: str, password: str) -> UserModel:
        user = UserModel(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=_hash_password(password),
            auth_provider="email",
            plan="trial",
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
        )
        self.session.add(user)
        self.session.flush()
        return user

    def get_by_id(self, user_id) -> UserModel | None:
        # Ensure user_id is a proper UUID object for cross-dialect compatibility
        if isinstance(user_id, str):
            user_id = _uuid.UUID(user_id)
        return self.session.query(UserModel).filter(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None)
        ).first()

    def get_by_email(self, email: str) -> UserModel | None:
        return self.session.query(UserModel).filter(
            UserModel.email == email.lower().strip(),
            UserModel.deleted_at.is_(None)
        ).first()

    def get_by_google_id(self, google_id: str) -> UserModel | None:
        return self.session.query(UserModel).filter(
            UserModel.google_id == google_id,
            UserModel.deleted_at.is_(None)
        ).first()

    def create_or_update_google_user(
        self, google_id: str, email: str, name: str, avatar_url: str = None
    ) -> UserModel:
        user = self.get_by_google_id(google_id)
        if user:
            user.name = name
            user.avatar_url = avatar_url
            user.updated_at = datetime.now(timezone.utc)
        else:
            user = self.get_by_email(email)
            if user:
                user.google_id = google_id
                user.auth_provider = "google"
                user.avatar_url = avatar_url
            else:
                user = UserModel(
                    email=email.lower().strip(),
                    name=name,
                    google_id=google_id,
                    auth_provider="google",
                    avatar_url=avatar_url,
                    plan="trial",
                    trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
                )
                self.session.add(user)
        self.session.flush()
        return user

    @staticmethod
    def verify_password(user: UserModel, password: str) -> bool:
        if not user.password_hash:
            return False
        return _check_password(password, user.password_hash)

    @staticmethod
    def is_trial_expired(user: UserModel) -> bool:
        if user.plan != "trial":
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at
