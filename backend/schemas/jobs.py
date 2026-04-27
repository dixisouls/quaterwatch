from pydantic import BaseModel, field_validator, Field
from typing import Any
import uuid
from datetime import datetime
import re

from backend.models.models import JobStatus


class JobCreate(BaseModel):
    ticker: str
    quarter: str  # "Q1", "Q2", "Q3", "Q4"
    year: int

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_valid(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{1,5}$", v):
            raise ValueError("Ticker must be 1-5 uppercase letters")
        return v

    @field_validator("quarter")
    @classmethod
    def quarter_must_be_valid(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in ("Q1", "Q2", "Q3", "Q4"):
            raise ValueError("Quarter must be Q1, Q2, Q3, or Q4")
        return v

    @field_validator("year")
    @classmethod
    def year_must_be_valid(cls, v: int) -> int:
        if v < 2000 or v > 2030:
            raise ValueError("Year must be between 2000 and 2030")
        return v


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID = Field(alias="id")
    status: JobStatus
    ticker: str
    quarter: str
    year: int
    error_message: str | None = None
    segmentation_notice: str | None = None
    pipeline_stage: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class TranscriptUpload(BaseModel):
    text: str


class SentimentOut(BaseModel):
    status: str
    score: float | None = None
    magnitude: float | None = None

    model_config = {"from_attributes": True}


class ConfidenceOut(BaseModel):
    score: float | None = None
    scoring_method: str
    key_phrases: list[str] | None = None
    hedging_phrases: list[str] | None = None

    model_config = {"from_attributes": True}


class EntityOut(BaseModel):
    name: str
    entity_type: str | None = None
    source: str | None = None
    salience: float | None = None

    model_config = {"from_attributes": True}


class SummaryOut(BaseModel):
    text: str
    key_points: list[str] | None = None
    summary_method: str
    faithfulness_score: float | None = None
    faithfulness_status: str
    flagged_claims: list[Any] | None = None

    model_config = {"from_attributes": True}


class SegmentOut(BaseModel):
    id: uuid.UUID
    name: str
    order_index: int
    text: str
    word_count: int
    sentiment: SentimentOut | None = None
    confidence: ConfidenceOut | None = None
    entities: list[EntityOut] = []
    summary: SummaryOut | None = None

    model_config = {"from_attributes": True}


class PriceDataOut(BaseModel):
    call_date: str | None = None
    price_on_call_date: float | None = None
    price_day_after: float | None = None
    price_week_after: float | None = None
    price_available: bool

    model_config = {"from_attributes": True}


class JobResults(BaseModel):
    job_id: uuid.UUID = Field(alias="id")
    ticker: str
    quarter: str
    year: int
    status: JobStatus
    segmentation_notice: str | None = None
    segments: list[SegmentOut] = []
    price_data: PriceDataOut | None = None

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: uuid.UUID
    ticker: str
    quarter: str
    year: int
    status: JobStatus
    created_at: datetime

    model_config = {"from_attributes": True}
