"""Shared test fixtures."""

import pytest
from unittest.mock import patch
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.db_models import *  # noqa: ensure all models registered


def _sqlite_compat_engine():
    """Create a SQLite in-memory engine with PostgreSQL type overrides."""
    engine = create_engine("sqlite:///:memory:")

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
    """
    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = SQLiteTypeCompiler.visit_JSON

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


@pytest.fixture
def app(test_engine):
    """Create a Flask test app with SQLite-backed DB sessions."""
    TestSession = sessionmaker(bind=test_engine)

    @contextmanager
    def _test_get_db():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Patch get_db before importing the app factory
    with patch("app.db.get_db", _test_get_db), \
         patch("app.api.auth.get_db", _test_get_db), \
         patch("app.middleware.auth.get_db", _test_get_db):
        from app import create_app
        flask_app = create_app()
        flask_app.config["TESTING"] = True
        # Store patched get_db so tests can use it
        flask_app._test_get_db = _test_get_db
        yield flask_app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
