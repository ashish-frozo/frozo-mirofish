"""Prediction validation model for storing BettaFish validation results."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..db import Base


def utcnow():
    return datetime.now(timezone.utc)


class PredictionValidationModel(Base):
    __tablename__ = "prediction_validations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_task_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    bettafish_prediction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    accuracy_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_trajectory: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    per_prediction: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
