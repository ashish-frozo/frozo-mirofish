"""Base repository with common CRUD operations."""

from sqlalchemy.orm import Session
from ..db import get_db


class BaseRepository:
    """Base class for all repositories. Provides session management."""

    @staticmethod
    def get_session():
        return get_db()
