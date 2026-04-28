import logging
from google.cloud import language_v1
from google.api_core.exceptions import GoogleAPIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.models.models import SentimentResult, SentimentStatus, Segment
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("worker.sentiment")

MIN_WORD_COUNT = 50


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type(GoogleAPIError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_nl_api(text: str) -> tuple[float, float]:
    """
    Calls the NL API analyze_sentiment endpoint.
    Returns (score, magnitude). Raises on failure, tenacity handles retries.
    """

    client = language_v1.LanguageServiceAsyncClient()
    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
    )
    request = language_v1.AnalyzeSentimentRequest(
        document=document,
    )
    response = await client.analyze_sentiment(request=request)
    sentiment = response.document_sentiment
    return sentiment.score, sentiment.magnitude

async def analyze_sentiment_for_segment(
    segment: Segment,
) -> SentimentResult:
    """
    Runs sentiment analysis for a single sentiment.

    - If word count < MIN_WORD_COUNT: markks as insufficient_data, no API call
    - If API success: stores score and magnitude, makrs as available
    - If all retries fail: marks as unavailable, does not raise

    Returns an unsaved SentimentResult ORM object.
    """
    if segment.word_count < MIN_WORD_COUNT:
        logger.info(
            f"[sentiment] Segment {segment.id} | {segment.name} has {segment.word_count} words,"
            f"below minimum {MIN_WORD_COUNT} words. Marking as insufficient_data."
        )
        return SentimentResult(
            segment_id=segment.id,
            status=SentimentStatus.insufficient_data,
            score=None,
            magnitude=None,
        )
    try:
        score, magnitude = await _call_nl_api(segment.text)
        logger.info(
            f"[sentiment] Segment {segment.id} | {segment.name} : score={score:.3f}, magnitude={magnitude:.3f}"
        )
        return SentimentResult(
            segment_id=segment.id,
            status=SentimentStatus.available,
            score=score,
            magnitude=magnitude,
        )
    except Exception as e:
        logger.error(
            f"[sentiment] All retries failed for segment {segment.id} : {e}"
            f"Marking as unavailable."
        )
        return SentimentResult(
            segment_id=segment.id,
            status=SentimentStatus.unavailable,
            score=None,
            magnitude=None,
        )

async def run_sentiment_for_job(db: AsyncSession, job_id: uuid.UUID) -> list[SentimentResult]:
    """
    Fetches all segments for the job from DB, runs sentiment analysis on each.
    A failure on one segment does not block the rest.
    Returns a list of unsaved SentimentResult ORM objects.
    """
    result = await db.execute(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.order_index)
    )
    segments = result.scalars().all()
    results = await asyncio.gather(
        *[analyze_sentiment_for_segment(segment) for segment in segments],
    )
    return list(results)