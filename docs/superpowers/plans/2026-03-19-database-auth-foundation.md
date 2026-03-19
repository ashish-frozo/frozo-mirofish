# Database & Auth Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PostgreSQL database, SQLAlchemy ORM, JWT authentication with Google OAuth, and a user dashboard to MiroFish — replacing the in-memory TaskManager and establishing the foundation for full data migration.

**Architecture:** Repository pattern over SQLAlchemy 2.0 models. Auth via JWT access/refresh tokens in httpOnly cookies with CSRF double-submit. Flask middleware injects `g.current_user` on protected routes. TaskManager singleton replaced with DB-backed TaskRepository. Frontend adds Pinia auth store, login/signup views, and route guards.

**Tech Stack:** PostgreSQL, SQLAlchemy 2.0, Alembic, passlib[bcrypt], python-jose, authlib, flask-limiter, Pinia

**Spec:** `docs/superpowers/specs/2026-03-19-database-multitenancy-auth-design.md`

---

## File Structure

### New Files (Backend)

| File | Responsibility |
|------|---------------|
| `backend/app/db.py` | SQLAlchemy engine, session factory, Base declarative class |
| `backend/app/models/db_models.py` | All 13 SQLAlchemy table models |
| `backend/app/repositories/__init__.py` | Repository exports |
| `backend/app/repositories/base.py` | BaseRepository with session management |
| `backend/app/repositories/user_repo.py` | User CRUD + auth queries |
| `backend/app/repositories/task_repo.py` | Task CRUD (replaces TaskManager) |
| `backend/app/api/auth.py` | Auth blueprint: signup, login, refresh, logout, Google OAuth |
| `backend/app/middleware/__init__.py` | Middleware exports |
| `backend/app/middleware/auth.py` | `@require_auth`, `@require_active_plan`, CSRF verification |
| `backend/app/middleware/errors.py` | Centralized error handler |
| `backend/alembic.ini` | Alembic config |
| `backend/alembic/env.py` | Alembic environment |
| `backend/alembic/versions/001_initial_schema.py` | Initial migration |
| `backend/tests/__init__.py` | Test package |
| `backend/tests/conftest.py` | Test fixtures (test DB, test client, auth helpers) |
| `backend/tests/test_auth.py` | Auth endpoint tests |
| `backend/tests/test_task_repo.py` | TaskRepository tests |
| `backend/tests/test_middleware.py` | Auth middleware tests |

### New Files (Frontend)

| File | Responsibility |
|------|---------------|
| `frontend/src/store/auth.js` | Pinia auth store (user, tokens, trial state) |
| `frontend/src/views/Login.vue` | Login page (email/password + Google OAuth button) |
| `frontend/src/views/Signup.vue` | Signup page |
| `frontend/src/views/Dashboard.vue` | Project list with status badges, resume links |
| `frontend/src/api/auth.js` | Auth API wrapper (signup, login, refresh, logout, me) |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/__init__.py` | Register auth blueprint, error handlers, startup recovery |
| `backend/app/config.py` | Add DATABASE_URL, JWT_*, GOOGLE_* config vars |
| `backend/app/models/task.py` | Deprecate TaskManager, redirect to TaskRepository |
| `backend/app/api/graph.py` | Add `@require_auth`, pass `user_id` to operations |
| `backend/app/api/simulation.py` | Add `@require_auth`, pass `user_id` to operations |
| `backend/app/api/report.py` | Add `@require_auth`, pass `user_id` to operations |
| `backend/pyproject.toml` | Add new dependencies |
| `frontend/package.json` | Add pinia |
| `frontend/src/main.js` | Register Pinia |
| `frontend/src/api/index.js` | Add auth interceptor, CSRF token, auto-refresh |
| `frontend/src/router/index.js` | Add auth routes, navigation guards |

---

## Task 1: Add Backend Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add database and auth dependencies to pyproject.toml**

Add to the `dependencies` list in `backend/pyproject.toml`:

```toml
    # Database
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg2-binary>=2.9",

    # Authentication
    "passlib[bcrypt]>=1.7",
    "python-jose[cryptography]>=3.3",
    "authlib>=1.3",
    "flask-limiter>=3.5",
```

- [ ] **Step 2: Install dependencies**

Run: `cd backend && uv sync`
Expected: All new packages install successfully.

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "deps: add SQLAlchemy, Alembic, JWT, OAuth, and rate limiter packages"
```

---

## Task 2: Database Engine & Config

**Files:**
- Create: `backend/app/db.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add database config vars to Config class**

Add these to `backend/app/config.py` after the existing config:

```python
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/mirofish')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '900'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '604800'))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')

    # File storage
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '../uploads'))
```

Also update `validate()` to make `DATABASE_URL` optional in dev (SQLite fallback) but warn:

```python
    @classmethod
    def validate(cls):
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is not configured")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY is not configured")
        if cls.JWT_SECRET_KEY == 'dev-secret-change-in-production':
            import logging
            logging.getLogger('mirofish').warning("JWT_SECRET_KEY is using default dev value — set it in production!")
        return errors
```

- [ ] **Step 2: Create database engine module**

Create `backend/app/db.py`:

```python
"""
Database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from contextlib import contextmanager

from .config import Config


class Base(DeclarativeBase):
    pass


# Fix Railway's postgres:// URL (SQLAlchemy requires postgresql://)
db_url = Config.DATABASE_URL
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db() -> Session:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create all tables (for dev/testing only — use Alembic in production)."""
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 3: Verify import works**

Run: `cd backend && uv run python -c "from app.db import Base, engine, get_db; print('DB module OK')"`
Expected: `DB module OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/db.py backend/app/config.py
git commit -m "feat: add database engine, session management, and config vars"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `backend/app/models/db_models.py`

- [ ] **Step 1: Create all 13 database models**

Create `backend/app/models/db_models.py` with all models from the spec (users, refresh_tokens, projects, tasks, simulations, agent_profiles, simulation_actions, simulation_round_summaries, reports, report_sections, report_logs, chat_sessions, chat_messages).

Each model uses UUID primary keys, proper foreign keys with CASCADE, and indexes matching the spec. Use `mapped_column` with SQLAlchemy 2.0 style.

```python
"""
SQLAlchemy database models for MiroFish.
"""

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow():
    return datetime.now(timezone.utc)


def trial_default():
    return datetime.now(timezone.utc) + timedelta(days=14)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    plan: Mapped[str] = mapped_column(String(20), default="trial")
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=trial_default)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("ProjectModel", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("UserModel", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token_hash", "token_hash"),
    )


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    simulation_requirement: Mapped[str | None] = mapped_column(Text)
    graph_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="created")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    step_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    ontology: Mapped[dict | None] = mapped_column(JSONB)
    analysis_summary: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    chunk_size: Mapped[int] = mapped_column(Integer, default=500)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=50)
    seed_files: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("UserModel", back_populates="projects")
    simulations = relationship("SimulationModel", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSessionModel", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_user_id", "user_id"),
        Index("idx_projects_status", "status"),
    )


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("UserModel", back_populates="tasks")

    __table_args__ = (
        Index("idx_tasks_user_id", "user_id"),
        Index("idx_tasks_project_id", "project_id"),
        Index("idx_tasks_status", "status"),
    )


class SimulationModel(Base):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    simulation_id: Mapped[str | None] = mapped_column(String(255))
    enable_twitter: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_reddit: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    config_reasoning: Mapped[str | None] = mapped_column(Text)
    entity_types: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    twitter_status: Mapped[str | None] = mapped_column(String(50))
    reddit_status: Mapped[str | None] = mapped_column(String(50))
    max_rounds: Mapped[int] = mapped_column(Integer, default=10)
    twitter_current_round: Mapped[int] = mapped_column(Integer, default=0)
    reddit_current_round: Mapped[int] = mapped_column(Integer, default=0)
    agent_count: Mapped[int] = mapped_column(Integer, default=0)
    process_pid: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project = relationship("ProjectModel", back_populates="simulations")
    agent_profiles = relationship("AgentProfileModel", back_populates="simulation", cascade="all, delete-orphan")
    actions = relationship("SimulationActionModel", back_populates="simulation", cascade="all, delete-orphan")
    round_summaries = relationship("SimulationRoundSummaryModel", back_populates="simulation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_simulations_project_id", "project_id"),
    )


class AgentProfileModel(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    agent_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    personality: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    simulation = relationship("SimulationModel", back_populates="agent_profiles")

    __table_args__ = (
        Index("idx_agent_profiles_simulation_id", "simulation_id"),
    )


class SimulationActionModel(Base):
    __tablename__ = "simulation_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_index: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(255))
    platform: Mapped[str | None] = mapped_column(String(20))
    action_type: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str | None] = mapped_column(Text)
    target_id: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    simulation = relationship("SimulationModel", back_populates="actions")

    __table_args__ = (
        Index("idx_sim_actions_simulation_id", "simulation_id"),
        Index("idx_sim_actions_round", "simulation_id", "round"),
        Index("idx_sim_actions_agent", "simulation_id", "agent_index"),
    )


class SimulationRoundSummaryModel(Base):
    __tablename__ = "simulation_round_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    simulation = relationship("SimulationModel", back_populates="round_summaries")

    __table_args__ = (
        UniqueConstraint("simulation_id", "round", "platform"),
        Index("idx_round_summaries_simulation", "simulation_id"),
    )


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    simulation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"))
    graph_id: Mapped[str | None] = mapped_column(String(255))
    simulation_requirement: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    outline: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    markdown_content: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("ProjectModel", back_populates="reports")
    sections = relationship("ReportSectionModel", back_populates="report", cascade="all, delete-orphan")
    logs = relationship("ReportLogModel", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_reports_project_id", "project_id"),
        Index("idx_reports_simulation_id", "simulation_id"),
    )


class ReportSectionModel(Base):
    __tablename__ = "report_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    section_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report = relationship("ReportModel", back_populates="sections")

    __table_args__ = (
        Index("idx_report_sections_report_id", "report_id"),
    )


class ReportLogModel(Base):
    __tablename__ = "report_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    log_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entries: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report = relationship("ReportModel", back_populates="logs")

    __table_args__ = (
        Index("idx_report_logs_report_id", "report_id"),
    )


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_index: Mapped[int | None] = mapped_column(Integer)
    agent_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project = relationship("ProjectModel", back_populates="chat_sessions")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chat_sessions_project_id", "project_id"),
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session = relationship("ChatSessionModel", back_populates="messages")

    __table_args__ = (
        Index("idx_chat_messages_session_id", "session_id"),
    )
```

- [ ] **Step 2: Verify models import cleanly**

Run: `cd backend && uv run python -c "from app.models.db_models import UserModel, ProjectModel, TaskModel; print(f'{len(UserModel.__table__.columns)} user columns OK')"`
Expected: `12 user columns OK` (or similar count)

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/db_models.py
git commit -m "feat: add all 13 SQLAlchemy database models"
```

---

## Task 4: Alembic Setup & Initial Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)

- [ ] **Step 1: Initialize Alembic**

Run: `cd backend && uv run alembic init alembic`

- [ ] **Step 2: Configure alembic.ini**

Edit `backend/alembic.ini` — set `sqlalchemy.url` to empty (we'll use env.py):

```ini
sqlalchemy.url =
```

- [ ] **Step 3: Configure alembic/env.py**

Replace the generated `env.py` target_metadata with:

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import Base, engine
from app.models.db_models import *  # noqa: import all models so Base.metadata is populated

target_metadata = Base.metadata

def run_migrations_online():
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

- [ ] **Step 4: Generate initial migration**

Run: `cd backend && uv run alembic revision --autogenerate -m "initial schema"`
Expected: Migration file created in `alembic/versions/`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic migration setup with initial schema"
```

---

## Task 5: Base Repository & Test Infrastructure

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/base.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create base repository**

Create `backend/app/repositories/base.py`:

```python
"""Base repository with common CRUD operations."""

from sqlalchemy.orm import Session
from ..db import get_db


class BaseRepository:
    """Base class for all repositories. Provides session management."""

    @staticmethod
    def get_session():
        return get_db()
```

Create `backend/app/repositories/__init__.py`:

```python
from .base import BaseRepository
```

- [ ] **Step 2: Create test infrastructure**

Create `backend/tests/__init__.py` (empty).

Create `backend/tests/conftest.py`:

```python
"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine):
    """Create a fresh DB session per test."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

- [ ] **Step 3: Verify test setup**

Run: `cd backend && uv run pytest tests/ -v --co`
Expected: Shows test collection (no tests yet, but no errors)

- [ ] **Step 4: Commit**

```bash
git add backend/app/repositories/ backend/tests/
git commit -m "feat: add base repository and test infrastructure"
```

---

## Task 6: User Repository

**Files:**
- Create: `backend/app/repositories/user_repo.py`
- Create: `backend/tests/test_user_repo.py`

- [ ] **Step 1: Write failing tests for UserRepository**

Create `backend/tests/test_user_repo.py`:

```python
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
        assert user.password_hash != "securepass123"  # should be hashed
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

    def test_create_or_update_google_user(self, db_session):
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

    def test_is_trial_expired(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(email="trial@example.com", name="Trial", password="pass")
        assert repo.is_trial_expired(user) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_user_repo.py -v`
Expected: FAIL (UserRepository does not exist)

- [ ] **Step 3: Implement UserRepository**

Create `backend/app/repositories/user_repo.py`:

```python
"""User repository — handles all user-related database operations."""

from datetime import datetime, timedelta, timezone
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from ..models.db_models import UserModel


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, email: str, name: str, password: str) -> UserModel:
        user = UserModel(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=bcrypt.using(rounds=12).hash(password),
            auth_provider="email",
            plan="trial",
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
        )
        self.session.add(user)
        self.session.flush()
        return user

    def get_by_id(self, user_id) -> UserModel | None:
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
            # Check if email already exists (link accounts)
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
        return bcrypt.verify(password, user.password_hash)

    @staticmethod
    def is_trial_expired(user: UserModel) -> bool:
        if user.plan != "trial":
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_user_repo.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/user_repo.py backend/tests/test_user_repo.py
git commit -m "feat: add UserRepository with create, auth, and Google OAuth support"
```

---

## Task 7: Task Repository (Replace TaskManager)

**Files:**
- Create: `backend/app/repositories/task_repo.py`
- Create: `backend/tests/test_task_repo.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_task_repo.py`:

```python
"""Tests for TaskRepository."""

import pytest
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository


class TestTaskRepository:
    @pytest.fixture
    def user(self, db_session):
        repo = UserRepository(db_session)
        return repo.create(email="taskuser@test.com", name="Task User", password="pass123")

    def test_create_task(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="ontology_generation", project_id=None)
        assert task.status == "pending"
        assert task.type == "ontology_generation"
        assert task.user_id == user.id

    def test_update_progress(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="graph_build")
        repo.update_progress(task.id, status="running", progress=50, message="Building...")
        refreshed = repo.get_by_id(task.id)
        assert refreshed.status == "running"
        assert refreshed.progress == 50

    def test_find_stale_running(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="simulation_run")
        repo.update_progress(task.id, status="running")
        stale = repo.find_by_status("running")
        assert len(stale) >= 1

    def test_complete_task(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="report_generation")
        repo.complete(task.id, result={"report_id": "abc123"})
        refreshed = repo.get_by_id(task.id)
        assert refreshed.status == "completed"
        assert refreshed.result == {"report_id": "abc123"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_task_repo.py -v`
Expected: FAIL

- [ ] **Step 3: Implement TaskRepository**

Create `backend/app/repositories/task_repo.py`:

```python
"""Task repository — replaces in-memory TaskManager."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import TaskModel


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id, task_type: str, project_id=None, metadata: dict = None) -> TaskModel:
        task = TaskModel(
            user_id=user_id,
            project_id=project_id,
            type=task_type,
            status="pending",
            metadata_=metadata or {},
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get_by_id(self, task_id) -> TaskModel | None:
        return self.session.query(TaskModel).filter(TaskModel.id == task_id).first()

    def update_progress(self, task_id, status: str = None, progress: int = None, message: str = None):
        task = self.get_by_id(task_id)
        if not task:
            return
        if status:
            task.status = status
            if status == "running" and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
        if progress is not None:
            task.progress = progress
        if message:
            task.message = message
        self.session.flush()

    def complete(self, task_id, result: dict = None):
        task = self.get_by_id(task_id)
        if not task:
            return
        task.status = "completed"
        task.progress = 100
        task.result = result
        task.completed_at = datetime.now(timezone.utc)
        self.session.flush()

    def fail(self, task_id, error: str):
        task = self.get_by_id(task_id)
        if not task:
            return
        task.status = "failed"
        task.error = error
        task.completed_at = datetime.now(timezone.utc)
        self.session.flush()

    def find_by_status(self, status: str) -> list[TaskModel]:
        return self.session.query(TaskModel).filter(TaskModel.status == status).all()

    def recover_stale(self):
        """Mark all 'running' tasks as failed (called on server startup)."""
        stale = self.find_by_status("running")
        for task in stale:
            task.status = "failed"
            task.error = "Server restarted during execution. Please retry."
            task.completed_at = datetime.now(timezone.utc)
        self.session.flush()
        return len(stale)
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest tests/test_task_repo.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/task_repo.py backend/tests/test_task_repo.py
git commit -m "feat: add TaskRepository to replace in-memory TaskManager"
```

---

## Task 8: Auth Middleware

**Files:**
- Create: `backend/app/middleware/__init__.py`
- Create: `backend/app/middleware/auth.py`
- Create: `backend/app/middleware/errors.py`

- [ ] **Step 1: Create auth middleware**

Create `backend/app/middleware/__init__.py`:

```python
from .auth import require_auth, require_active_plan
from .errors import register_error_handlers
```

Create `backend/app/middleware/auth.py`:

```python
"""Authentication middleware."""

import functools
import hashlib
from datetime import datetime, timezone

from flask import request, g, jsonify, current_app
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
    """Decorator: require valid JWT. Sets g.current_user."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token_from_request()
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            return jsonify({"error": "Invalid or expired token"}), 401

        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "Invalid token payload"}), 401

        with get_db() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 401

            g.current_user = user
            g.db_session = session
            return f(*args, **kwargs)

    return decorated


def require_active_plan(f):
    """Decorator: require non-expired trial or active paid plan."""
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
```

- [ ] **Step 2: Create centralized error handler**

Create `backend/app/middleware/errors.py`:

```python
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
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500
```

- [ ] **Step 3: Verify imports**

Run: `cd backend && uv run python -c "from app.middleware import require_auth, require_active_plan, register_error_handlers; print('Middleware OK')"`
Expected: `Middleware OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/middleware/
git commit -m "feat: add auth middleware, trial enforcement, and centralized error handling"
```

---

## Task 9: Auth API Endpoints

**Files:**
- Create: `backend/app/api/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests for auth endpoints**

Create `backend/tests/test_auth.py` with tests for:
- `POST /api/auth/signup` — creates user, returns tokens
- `POST /api/auth/login` — valid credentials return tokens
- `POST /api/auth/login` — invalid credentials return 401
- `POST /api/auth/refresh` — valid refresh token returns new access token
- `GET /api/auth/me` — returns current user profile
- `POST /api/auth/logout` — revokes refresh token

```python
"""Tests for auth endpoints."""

import pytest
from app import create_app
from app.db import Base

@pytest.fixture
def app(test_engine):
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestAuthSignup:
    def test_signup_success(self, client):
        resp = client.post("/api/auth/signup", json={
            "email": "new@example.com",
            "name": "New User",
            "password": "securepass123"
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_signup_duplicate_email(self, client):
        client.post("/api/auth/signup", json={
            "email": "dupe@example.com", "name": "First", "password": "pass123"
        })
        resp = client.post("/api/auth/signup", json={
            "email": "dupe@example.com", "name": "Second", "password": "pass123"
        })
        assert resp.status_code == 409

    def test_signup_short_password(self, client):
        resp = client.post("/api/auth/signup", json={
            "email": "short@example.com", "name": "Short", "password": "abc"
        })
        assert resp.status_code == 422

class TestAuthLogin:
    def test_login_success(self, client):
        client.post("/api/auth/signup", json={
            "email": "login@example.com", "name": "Login", "password": "pass123"
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com", "password": "pass123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/signup", json={
            "email": "wrong@example.com", "name": "Wrong", "password": "correct"
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrong@example.com", "password": "incorrect"
        })
        assert resp.status_code == 401

class TestAuthMe:
    def test_me_authenticated(self, client):
        signup = client.post("/api/auth/signup", json={
            "email": "me@example.com", "name": "Me", "password": "pass123"
        })
        token = signup.get_json()["access_token"]
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json()["email"] == "me@example.com"

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_auth.py -v`
Expected: FAIL

- [ ] **Step 3: Implement auth blueprint**

Create `backend/app/api/auth.py` implementing:
- `POST /signup` — validate input, create user via UserRepository, generate JWT tokens, store refresh token hash
- `POST /login` — verify credentials, generate tokens (rate limited: 5/min per IP)
- `POST /refresh` — validate refresh token, rotate (issue new, revoke old), return new access token
- `POST /logout` — revoke refresh token
- `GET /me` — return current user profile (requires `@require_auth`)
- `PUT /me` — update profile (requires `@require_auth`)
- `GET /google` — redirect to Google OAuth consent screen
- `GET /google/callback` — handle Google OAuth callback, create/update user, return tokens

Token generation helper:
```python
def _generate_tokens(user):
    access_token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)},
        Config.JWT_SECRET_KEY, algorithm="HS256"
    )
    refresh_token = secrets.token_urlsafe(64)
    # Store hash of refresh token in DB
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    # Save to refresh_tokens table...
    return access_token, refresh_token
```

- [ ] **Step 4: Register auth blueprint in app factory**

Add to `backend/app/__init__.py`:

```python
from .api.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

from .middleware.errors import register_error_handlers
register_error_handlers(app)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && uv run pytest tests/test_auth.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/auth.py backend/tests/test_auth.py backend/app/__init__.py
git commit -m "feat: add auth endpoints — signup, login, refresh, logout, Google OAuth"
```

---

## Task 10: Protect Existing API Endpoints

**Files:**
- Modify: `backend/app/api/graph.py`
- Modify: `backend/app/api/simulation.py`
- Modify: `backend/app/api/report.py`

- [ ] **Step 1: Add `@require_auth` to all graph endpoints**

Import and apply decorator to every route in `backend/app/api/graph.py`:

```python
from ..middleware.auth import require_auth

@graph_bp.route('/ontology/generate', methods=['POST'])
@require_auth
def generate_ontology():
    user = g.current_user
    # ... existing code ...
```

Apply to all routes in the file. Pass `g.current_user.id` where user context is needed.

- [ ] **Step 2: Add `@require_auth` to all simulation endpoints**

Same pattern for `backend/app/api/simulation.py`.

- [ ] **Step 3: Add `@require_auth` to all report endpoints**

Same pattern for `backend/app/api/report.py`.

- [ ] **Step 4: Test that unauthenticated requests get 401**

Run: `curl -s http://localhost:5001/api/graph/ontology/generate -X POST | python3 -c "import sys,json; print(json.load(sys.stdin))"`
Expected: `{'error': 'Authentication required'}`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/graph.py backend/app/api/simulation.py backend/app/api/report.py
git commit -m "feat: protect all API endpoints with @require_auth"
```

---

## Task 11: Frontend — Add Pinia & Auth Store

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.js`
- Create: `frontend/src/store/auth.js`
- Create: `frontend/src/api/auth.js`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: Install Pinia**

Run: `cd frontend && npm install pinia`

- [ ] **Step 2: Register Pinia in main.js**

Edit `frontend/src/main.js`:

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 3: Create auth API wrapper**

Create `frontend/src/api/auth.js`:

```javascript
import service from './index'

export const signup = (data) => service.post('/api/auth/signup', data)
export const login = (data) => service.post('/api/auth/login', data)
export const refreshToken = (token) => service.post('/api/auth/refresh', { refresh_token: token })
export const logout = () => service.post('/api/auth/logout')
export const getMe = () => service.get('/api/auth/me')
export const updateMe = (data) => service.put('/api/auth/me', data)
```

- [ ] **Step 4: Create auth store**

Create `frontend/src/store/auth.js`:

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshTokenValue = ref(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const isTrialExpired = computed(() => {
    if (!user.value || user.value.plan !== 'trial') return false
    return new Date(user.value.trial_ends_at) < new Date()
  })
  const trialDaysLeft = computed(() => {
    if (!user.value || user.value.plan !== 'trial') return null
    const diff = new Date(user.value.trial_ends_at) - new Date()
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
  })

  function setTokens(access, refresh) {
    accessToken.value = access
    refreshTokenValue.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    refreshTokenValue.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function signupAction(email, name, password) {
    const res = await authApi.signup({ email, name, password })
    setTokens(res.access_token, res.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function loginAction(email, password) {
    const res = await authApi.login({ email, password })
    setTokens(res.access_token, res.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function logoutAction() {
    try { await authApi.logout() } catch (e) { /* ignore */ }
    clearTokens()
    router.push('/login')
  }

  async function fetchUser() {
    try {
      const res = await authApi.getMe()
      user.value = res.user || res
    } catch (e) {
      clearTokens()
    }
  }

  async function refreshAccessToken() {
    if (!refreshTokenValue.value) throw new Error('No refresh token')
    const res = await authApi.refreshToken(refreshTokenValue.value)
    setTokens(res.access_token, res.refresh_token)
  }

  return {
    user, accessToken, refreshTokenValue,
    isAuthenticated, isTrialExpired, trialDaysLeft,
    signupAction, loginAction, logoutAction, fetchUser, refreshAccessToken, clearTokens
  }
})
```

- [ ] **Step 5: Add auth interceptor to Axios**

Edit `frontend/src/api/index.js` — add request interceptor for Bearer token and response interceptor for 401 auto-refresh:

```javascript
import { useAuthStore } from '../store/auth'

// Request interceptor — attach token
service.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Response interceptor — auto-refresh on 401
service.interceptors.response.use(
  response => { /* existing success handler */ },
  async error => {
    const auth = useAuthStore()
    if (error.response?.status === 401 && auth.refreshTokenValue && !error.config._retry) {
      error.config._retry = true
      try {
        await auth.refreshAccessToken()
        error.config.headers.Authorization = `Bearer ${auth.accessToken}`
        return service(error.config)
      } catch (refreshError) {
        auth.clearTokens()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/src/main.js frontend/src/store/auth.js frontend/src/api/auth.js frontend/src/api/index.js
git commit -m "feat: add Pinia auth store, auth API, and token interceptor"
```

---

## Task 12: Frontend — Login & Signup Pages

**Files:**
- Create: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/Signup.vue`
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Create Login.vue**

Create `frontend/src/views/Login.vue` with:
- Email/password form
- "Sign in with Google" button
- Link to signup page
- Error display for invalid credentials
- Calls `authStore.loginAction(email, password)`

- [ ] **Step 2: Create Signup.vue**

Create `frontend/src/views/Signup.vue` with:
- Email/name/password/confirm-password form
- "Sign up with Google" button
- Link to login page
- Password validation (min 8 chars)
- Calls `authStore.signupAction(email, name, password)`

- [ ] **Step 3: Add routes and navigation guards**

Edit `frontend/src/router/index.js`:

```javascript
import { useAuthStore } from '../store/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/signup', name: 'Signup', component: () => import('../views/Signup.vue'), meta: { public: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  // ... existing routes (all protected by default)
]

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (!auth.isAuthenticated) return next('/login')
  next()
})
```

- [ ] **Step 4: Test login flow manually**

Open browser, navigate to `/login`, verify redirect works.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/Login.vue frontend/src/views/Signup.vue frontend/src/router/index.js
git commit -m "feat: add login and signup pages with route guards"
```

---

## Task 13: Frontend — Dashboard View

**Files:**
- Create: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Create Dashboard.vue**

Dashboard shows:
- User greeting + trial days remaining badge
- "New Project" button
- List of user's projects with: name, status badge, current step indicator, created date, resume button
- Empty state when no projects exist

Fetches from `GET /api/projects` (to be implemented in the data migration phase — for now, show empty state with "New Project" CTA).

- [ ] **Step 2: Update Home.vue to redirect authenticated users to dashboard**

```javascript
onMounted(() => {
  const auth = useAuthStore()
  if (auth.isAuthenticated) {
    router.push('/dashboard')
  }
})
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Dashboard.vue frontend/src/views/Home.vue
git commit -m "feat: add user dashboard with project list and trial badge"
```

---

## Task 14: Integration Test & Deploy

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Add PostgreSQL to Railway**

In Railway dashboard: Add PostgreSQL plugin to the project. Copy `DATABASE_URL` and add to service environment variables.

Also add: `JWT_SECRET_KEY` (generate with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`)

- [ ] **Step 3: Run Alembic migration on Railway**

```bash
railway run "cd backend && uv run alembic upgrade head"
```

- [ ] **Step 4: Push and deploy**

```bash
git push frozo main
railway up --detach
```

- [ ] **Step 5: Verify deployment**

```bash
curl https://frozo-mirofish-production.up.railway.app/health
curl -X POST https://frozo-mirofish-production.up.railway.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test","password":"testpass123"}'
```

Expected: Health OK, signup returns tokens.

- [ ] **Step 6: Commit any final fixes**

```bash
git add -A && git commit -m "fix: integration test fixes for deployment"
```

---

## Summary

| Task | What | Estimated Time |
|------|------|---------------|
| 1 | Backend dependencies | 2 min |
| 2 | DB engine & config | 5 min |
| 3 | SQLAlchemy models (13 tables) | 10 min |
| 4 | Alembic setup | 5 min |
| 5 | Base repository & test infra | 5 min |
| 6 | User repository + tests | 10 min |
| 7 | Task repository + tests | 10 min |
| 8 | Auth middleware | 5 min |
| 9 | Auth API endpoints + tests | 15 min |
| 10 | Protect existing endpoints | 10 min |
| 11 | Frontend Pinia + auth store | 10 min |
| 12 | Login/Signup pages + router | 15 min |
| 13 | Dashboard view | 10 min |
| 14 | Integration test & deploy | 10 min |

**Phase 2 (next plan):** Migrate existing models (projects → simulations → reports → chat) from file-based to DB repositories.
