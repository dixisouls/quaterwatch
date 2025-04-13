import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Float, Integer, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    awaiting_upload = "awaiting_upload"
    complete = "complete"
    failed = "failed"


class SentimentStatus(str, enum.Enum):
    available = "available"
    insufficient_data = "insufficient_data"
    unavailable = "unavailable"


class ScoringMethod(str, enum.Enum):
    gemini = "gemini"
    heuristic = "heuristic"


class SummaryMethod(str, enum.Enum):
    generative = "generative"
    extractive = "extractive"


class FaithfulnessStatus(str, enum.Enum):
    verified = "verified"
    partially_verified = "partially_verified"
    unverified = "unverified"


# ── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="user")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    quarter: Mapped[str] = mapped_column(String(10), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.pending, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    transcript_gcs_path: Mapped[str | None] = mapped_column(Text)
    segmentation_notice: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="jobs")
    segments: Mapped[list["Segment"]] = relationship("Segment", back_populates="job")
    price_data: Mapped["PriceData | None"] = relationship("PriceData", back_populates="job", uselist=False)


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    job: Mapped["Job"] = relationship("Job", back_populates="segments")
    sentiment: Mapped["SentimentResult | None"] = relationship(
        "SentimentResult", back_populates="segment", uselist=False
    )
    confidence: Mapped["ConfidenceResult | None"] = relationship(
        "ConfidenceResult", back_populates="segment", uselist=False
    )
    entities: Mapped[list["Entity"]] = relationship("Entity", back_populates="segment")
    summary: Mapped["Summary | None"] = relationship(
        "Summary", back_populates="segment", uselist=False
    )


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False, unique=True
    )
    status: Mapped[SentimentStatus] = mapped_column(
        SAEnum(SentimentStatus), nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float)
    magnitude: Mapped[float | None] = mapped_column(Float)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="sentiment")


class ConfidenceResult(Base):
    __tablename__ = "confidence_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False, unique=True
    )
    score: Mapped[float | None] = mapped_column(Float)
    scoring_method: Mapped[ScoringMethod] = mapped_column(
        SAEnum(ScoringMethod), default=ScoringMethod.gemini
    )
    key_phrases: Mapped[list | None] = mapped_column(JSON)
    hedging_phrases: Mapped[list | None] = mapped_column(JSON)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="confidence")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50))  # "nl_api" or "gemini"
    salience: Mapped[float | None] = mapped_column(Float)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="entities")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False, unique=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list | None] = mapped_column(JSON)
    summary_method: Mapped[SummaryMethod] = mapped_column(
        SAEnum(SummaryMethod), default=SummaryMethod.generative
    )
    faithfulness_score: Mapped[float | None] = mapped_column(Float)
    faithfulness_status: Mapped[FaithfulnessStatus] = mapped_column(
        SAEnum(FaithfulnessStatus), default=FaithfulnessStatus.unverified
    )
    flagged_claims: Mapped[list | None] = mapped_column(JSON)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="summary")


class PriceData(Base):
    __tablename__ = "price_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True
    )
    call_date: Mapped[str | None] = mapped_column(String(20))
    price_on_call_date: Mapped[float | None] = mapped_column(Float)
    price_day_after: Mapped[float | None] = mapped_column(Float)
    price_week_after: Mapped[float | None] = mapped_column(Float)
    price_available: Mapped[bool] = mapped_column(Boolean, default=False)

    job: Mapped["Job"] = relationship("Job", back_populates="price_data")
