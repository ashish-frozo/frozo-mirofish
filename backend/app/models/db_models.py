"""
SQLAlchemy 2.0 ORM models for MiroFish.
All 13 models covering users, projects, simulations, reports, and chat.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)


def trial_default():
    return datetime.now(timezone.utc) + timedelta(days=14)


# ---------------------------------------------------------------------------
# 1. UserModel
# ---------------------------------------------------------------------------

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="email")
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="trial")
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=trial_default)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[list["ProjectModel"]] = relationship("ProjectModel", back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list["TaskModel"]] = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# 2. RefreshTokenModel
# ---------------------------------------------------------------------------

class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash"),
    )


# ---------------------------------------------------------------------------
# 3. ProjectModel
# ---------------------------------------------------------------------------

class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    simulation_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graph_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    step_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ontology: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    seed_files: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="projects")
    simulations: Mapped[list["SimulationModel"]] = relationship("SimulationModel", back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list["TaskModel"]] = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["ReportModel"]] = relationship("ReportModel", back_populates="project", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSessionModel"]] = relationship("ChatSessionModel", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_status", "status"),
    )


# ---------------------------------------------------------------------------
# 4. TaskModel
# ---------------------------------------------------------------------------

class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="tasks")
    project: Mapped[Optional["ProjectModel"]] = relationship("ProjectModel", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_user_id", "user_id"),
        Index("ix_tasks_project_id", "project_id"),
        Index("ix_tasks_status", "status"),
    )


# ---------------------------------------------------------------------------
# 5. SimulationModel
# ---------------------------------------------------------------------------

class SimulationModel(Base):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    simulation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enable_twitter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enable_reddit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    config_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    twitter_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reddit_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    twitter_current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reddit_current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    process_pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="simulations")
    agent_profiles: Mapped[list["AgentProfileModel"]] = relationship("AgentProfileModel", back_populates="simulation", cascade="all, delete-orphan")
    actions: Mapped[list["SimulationActionModel"]] = relationship("SimulationActionModel", back_populates="simulation", cascade="all, delete-orphan")
    round_summaries: Mapped[list["SimulationRoundSummaryModel"]] = relationship("SimulationRoundSummaryModel", back_populates="simulation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_simulations_project_id", "project_id"),
    )


# ---------------------------------------------------------------------------
# 6. AgentProfileModel
# ---------------------------------------------------------------------------

class AgentProfileModel(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    agent_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    profile_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    simulation: Mapped["SimulationModel"] = relationship("SimulationModel", back_populates="agent_profiles")

    __table_args__ = (
        Index("ix_agent_profiles_simulation_id", "simulation_id"),
    )


# ---------------------------------------------------------------------------
# 7. SimulationActionModel
# ---------------------------------------------------------------------------

class SimulationActionModel(Base):
    __tablename__ = "simulation_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_index: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    simulation: Mapped["SimulationModel"] = relationship("SimulationModel", back_populates="actions")

    __table_args__ = (
        Index("ix_simulation_actions_simulation_id", "simulation_id"),
        Index("ix_simulation_actions_simulation_id_round", "simulation_id", "round"),
        Index("ix_simulation_actions_simulation_id_agent_index", "simulation_id", "agent_index"),
    )


# ---------------------------------------------------------------------------
# 8. SimulationRoundSummaryModel
# ---------------------------------------------------------------------------

class SimulationRoundSummaryModel(Base):
    __tablename__ = "simulation_round_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    simulation: Mapped["SimulationModel"] = relationship("SimulationModel", back_populates="round_summaries")

    __table_args__ = (
        UniqueConstraint("simulation_id", "round", "platform", name="uq_round_summaries_sim_round_platform"),
        Index("ix_simulation_round_summaries_simulation_id", "simulation_id"),
    )


# ---------------------------------------------------------------------------
# 9. ReportModel
# ---------------------------------------------------------------------------

class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    simulation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="SET NULL"), nullable=True)
    graph_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    simulation_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outline: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    markdown_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="reports")
    sections: Mapped[list["ReportSectionModel"]] = relationship("ReportSectionModel", back_populates="report", cascade="all, delete-orphan")
    logs: Mapped[list["ReportLogModel"]] = relationship("ReportLogModel", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reports_project_id", "project_id"),
        Index("ix_reports_simulation_id", "simulation_id"),
    )


# ---------------------------------------------------------------------------
# 10. ReportSectionModel
# ---------------------------------------------------------------------------

class ReportSectionModel(Base):
    __tablename__ = "report_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    section_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    report: Mapped["ReportModel"] = relationship("ReportModel", back_populates="sections")

    __table_args__ = (
        Index("ix_report_sections_report_id", "report_id"),
    )


# ---------------------------------------------------------------------------
# 11. ReportLogModel
# ---------------------------------------------------------------------------

class ReportLogModel(Base):
    __tablename__ = "report_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    log_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    report: Mapped["ReportModel"] = relationship("ReportModel", back_populates="logs")

    __table_args__ = (
        Index("ix_report_logs_report_id", "report_id"),
    )


# ---------------------------------------------------------------------------
# 12. ChatSessionModel
# ---------------------------------------------------------------------------

class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessageModel"]] = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_sessions_project_id", "project_id"),
    )


# ---------------------------------------------------------------------------
# 13. ChatMessageModel
# ---------------------------------------------------------------------------

class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    session: Mapped["ChatSessionModel"] = relationship("ChatSessionModel", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
    )
