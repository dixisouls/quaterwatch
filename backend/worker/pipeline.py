import uuid
import logging
import asyncio

from backend.database import AsyncSessionLocal
from backend.models.models import JobStatus, Segment, SentimentResult, SentimentStatus
from backend.services.job_service import get_job_by_id, update_job_status
from backend.services.transcript_service import fetch_transcript

logger = logging.getLogger("worker.pipeline")


async def run_pipeline(job_id: uuid.UUID) -> None:
    """
    Phase 1 stub pipeline. Logs each stage and writes status updates.
    No real AI or API calls yet.
    """
    async with AsyncSessionLocal() as db:
        try:
            job = await get_job_by_id(db, job_id)
            if not job:
                logger.error(f"[pipeline] Job {job_id} not found")
                return

            await update_job_status(db, job_id, JobStatus.processing)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — status: processing")

            # Stage 1: Transcript fetch (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: transcript fetch")
            
            transcript_text = await fetch_transcript(job.ticker, job.quarter, job.year)

            if transcript_text is None:
                await update_job_status(db, job_id, JobStatus.awaiting_upload)
                await db.commit()
                logger.info(f"[pipeline] Job {job_id} — transcript not found, awaiting upload")
                return
            
            job.transcript_gcs_path = f"local:{job_id}"
            await db.flush()
            await db.commit()

            # Stage 2: Segmentation (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: segmentation (stub)")
            await asyncio.sleep(1)
            await _create_stub_segments(db, job_id)
            await db.commit()

            # Stage 3: Sentiment (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: sentiment scoring (stub)")
            await asyncio.sleep(1)

            # Stage 4: Confidence scoring (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: confidence scoring (stub)")
            await asyncio.sleep(1)

            # Stage 5: Named entity extraction (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: entity extraction (stub)")
            await asyncio.sleep(1)

            # Stage 6: Summarization (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: summarization (stub)")
            await asyncio.sleep(1)

            # Stage 7: Faithfulness check (stub)
            logger.info(f"[pipeline] Job {job_id} — stage: faithfulness check (stub)")
            await asyncio.sleep(1)

            await update_job_status(db, job_id, JobStatus.complete)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — status: complete")

        except Exception as exc:
            logger.exception(f"[pipeline] Job {job_id} failed: {exc}")
            async with AsyncSessionLocal() as err_db:
                await update_job_status(err_db, job_id, JobStatus.failed, str(exc))
                await err_db.commit()


async def _create_stub_segments(db, job_id: uuid.UUID) -> None:
    """Creates 3 stub segments so the results page has something to show."""
    stub_segments = [
        ("Opening Remarks", 0, "This is a stub for the opening remarks segment. Real transcript content will appear here after Phase 2."),
        ("CFO Financial Review", 1, "This is a stub for the CFO financial review segment. Real transcript content will appear here after Phase 2."),
        ("Q&A Session", 2, "This is a stub for the Q&A session segment. Real transcript content will appear here after Phase 2."),
    ]

    for name, order, text in stub_segments:
        segment = Segment(
            job_id=job_id,
            name=name,
            order_index=order,
            text=text,
            word_count=len(text.split()),
        )
        db.add(segment)
        await db.flush()

        sentiment = SentimentResult(
            segment_id=segment.id,
            status=SentimentStatus.unavailable,
        )
        db.add(sentiment)

    await db.flush()
