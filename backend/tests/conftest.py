"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine, event, String, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.db_models import *  # noqa: ensure all models registered


def _sqlite_compat_engine():
    """Create a SQLite in-memory engine with PostgreSQL type overrides."""
    engine = create_engine("sqlite:///:memory:")

    # Patch UUID columns to use String(36) for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _patch_pg_types_for_sqlite():
    """
    Override PostgreSQL-specific column types so they render under SQLite.
    Modifies the SQLAlchemy type registry for the duration of the test session.
    """
    from sqlalchemy.dialects.postgresql.base import PGTypeCompiler
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    # Make SQLite compiler handle JSONB as JSON
    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = SQLiteTypeCompiler.visit_JSON

    # Make SQLite compiler handle UUID as VARCHAR
    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):
        def visit_UUID(self, type_, **kw):
            return "VARCHAR(36)"
        SQLiteTypeCompiler.visit_UUID = visit_UUID


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for tests."""
    _patch_pg_types_for_sqlite()
    engine = _sqlite_compat_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine):
    """Create a fresh DB session per test with rollback."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
