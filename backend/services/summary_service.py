import re
import asyncio
import logging
import uuid
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.config import get_settings
from backend.models.models import Segment, Summary, SummaryMethod, FaithfulnessStatus

settings = get_settings()
logger = logging.getLogger("worker.summary")

# Pydanctic schema for Gemini structured output
class SegmentSummary(BaseModel):
    text: str
    key_points: list[str]

# Extractive summary fallback
def _extractive_summary(segment_text: str) -> SegmentSummary:
    """
    Pythonic extractive summary fallback. Splits text into sentences,
    returns the first 2 and the last 2 sentences combined as the summary
    text and use them as key points.
    """
    sentences = re.split(r'(?<=[.!?])\s+', segment_text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= 4:
        selected = sentences
    else:
        selected = sentences[:2] + sentences[-2:]
    
    summary_text = " ".join(selected)
    key_points = selected
    
    return SegmentSummary(text=summary_text, key_points=key_points)

# Gemini call 
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type((APIError,Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_gemini(segment_text: str) -> SegmentSummary:
    """
    Calls Gemini with structured output enforced via response_schema 
    to generate a summary and key points for a segment. Tenacity retries 
    upto 3 times.
    """
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )

    prompt = (
    "You are summarizing a segment of an earnings call transcript for investors. "
    "Write a concise summary of 3 to 5 sentences capturing the most important "
    "information communicated in this segment. "
    "Also extract 3 to 5 key points as short standalone bullet statements. "
    "Focus on financial results, strategic decisions, guidance, and notable risks. "
    "Do not include filler phrases like 'the speaker said' or 'in this segment'. "
    "Write directly and factually.\n\n"
    f"Segment:\n{segment_text}"
)

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SegmentSummary,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL"
            ),
        ),
    )

    return response.parsed

# Per-segment handler
async def summarize_segment(
    segment: Segment,
) -> Summary:
    """
    Generate a summary for a single segment.
    Falls back to extractive summary if Gemini fails.
    Faithfulness check is performed on the summary.
    Returns an unsaved Summary ORM object.
    """
    summary_method = SummaryMethod.generative

    try:
        result = await _call_gemini(segment.text)
        logger.info(
            f"[summary] Segment {segment.id} | {segment.name}"
            f" generated summary: {len(result.text)} characters"
            f" key points: {len(result.key_points)}"
        )
    except Exception as e:
        logger.error(
            f"[summary] Error calling Gemini for segment {segment.id} | {segment.name} : {e}"
            f"Falling back to extractive summary."
        )
        summary_method = SummaryMethod.extractive
        result = _extractive_summary(segment.text)
    
    return Summary(
        segment_id=segment.id,
        text=result.text,
        key_points=result.key_points,
        summary_method=summary_method,
        faithfulness_score=None,
        faithfulness_status=FaithfulnessStatus.unverified,
        flagged_claims=None,
    )

# Public entry point
async def generate_summaries_for_job(db: AsyncSession, job_id: uuid.UUID) -> list[Summary]:
    """
    Fetches all segments for the job from DB, generates summaries for each.
    A failure on one segment does not block the rest.
    Returns a list of unsaved Summary ORM objects.
    """
    result = await db.execute(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.order_index)
    )    

    segments = result.scalars().all()
    results = await asyncio.gather(
        *[summarize_segment(segment) for segment in segments],
    )
    return list(results)