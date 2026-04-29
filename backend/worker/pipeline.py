import uuid
import logging

from backend.database import AsyncSessionLocal
from backend.models.models import JobStatus, Segment, SentimentResult, SentimentStatus
from backend.services.job_service import get_job_by_id, update_job_status
from backend.services.transcript_service import fetch_transcript
from backend.services.storage_service import upload_transcript, download_transcript
from backend.services.segmentation_service import segment_transcript
from backend.services.sentiment_service import run_sentiment_for_job
from backend.services.confidence_service import score_confidence_for_job
from backend.services.entity_service import extract_entities_for_job
from backend.services.summary_service import generate_summaries_for_job
from backend.services.faithfulness_service import run_faithfulness_checks_for_job

logger = logging.getLogger("worker.pipeline")


async def run_pipeline(job_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        try:
            job = await get_job_by_id(db, job_id)
            if not job:
                logger.error(f"[pipeline] Job {job_id} not found")
                return

            await update_job_status(db, job_id, JobStatus.processing)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — status: processing")

            async def _set_stage(stage: int) -> None:
                job.pipeline_stage = stage
                await db.flush()

            # Stage 1: Transcript fetch
            await _set_stage(1)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: transcript fetch")

            transcript_text = None

            # If a GCS path already exists from a manual upload, download it from there
            if job.transcript_gcs_path and not job.transcript_gcs_path.startswith("local:"):
                logger.info(f"[pipeline] Job {job_id} — found existing GCS path, downloading")
                transcript_text = await download_transcript(job.transcript_gcs_path)
                if transcript_text is None:
                    logger.warning(f"[pipeline] Job {job_id} — failed to download transcript from GCS. Falling back to FMP")
            
            if transcript_text is None:
                transcript_text = await fetch_transcript(job.ticker, job.quarter, job.year)

            if transcript_text is None:
                await update_job_status(db, job_id, JobStatus.awaiting_upload)
                await db.commit()
                logger.info(f"[pipeline] Job {job_id} — transcript not found, awaiting upload")
                return

            # Upload to GCS if not already there
            if not job.transcript_gcs_path or job.transcript_gcs_path.startswith("local:"):
                gcs_path = await upload_transcript(str(job_id), transcript_text)
                job.transcript_gcs_path = gcs_path or f"upload-failed:{job_id}"
                await db.flush()
                await db.commit()

            # Stage 2: Segmentation
            await _set_stage(2)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: segmentation")

            segments, segment_notice = await segment_transcript(transcript_text)
            if segment_notice:
                job.segmentation_notice = segment_notice
                await db.flush()

            for order_index, seg in enumerate(segments):
                segment = Segment(
                    job_id=job_id,
                    name=seg["name"],
                    order_index=order_index,
                    text=seg["text"],
                    word_count=len(seg["text"].split()),
                )
                db.add(segment)
            await db.commit()

            logger.info(f"[segmentation] Created {len(segments)} segments for job {job_id}")

            # Stage 3: Sentiment
            await _set_stage(3)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: sentiment scoring")

            sentiment_results = await run_sentiment_for_job(db, job_id)
            for result in sentiment_results:
                db.add(result)
            await db.commit()
            logger.info(f"[sentiment] Stored {len(sentiment_results)} sentiment results for job {job_id}")

            # Stage 4: Confidence scoring
            await _set_stage(4)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: confidence scoring")

            confidence_results = await score_confidence_for_job(db, job_id)
            for result in confidence_results:
                db.add(result)
            await db.commit()
            logger.info(f"[confidence] Stored {len(confidence_results)} confidence results for job {job_id}")

            # Stage 5: Named entity extraction
            await _set_stage(5)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: entity extraction")

            entities = await extract_entities_for_job(db, job_id)
            for entity in entities:
                db.add(entity)
            await db.commit()
            logger.info(f"[entity] Stored {len(entities)} entities for job {job_id}")

            # Stage 6: Summarization
            await _set_stage(6)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: summarization (stub)")

            summaries = await generate_summaries_for_job(db, job_id)
            for summary in summaries:
                db.add(summary)
            await db.commit()
            logger.info(f"[summary] Stored {len(summaries)} summaries for job {job_id}")

            # Stage 7: Faithfulness check
            await _set_stage(7)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — stage: faithfulness check (stub)")

            await run_faithfulness_checks_for_job(db, job_id)
            await db.commit()
            logger.info(f"[faithfulness] Stored {len(summaries)} faithfulness results for job {job_id}")

            await update_job_status(db, job_id, JobStatus.complete)
            await db.commit()
            logger.info(f"[pipeline] Job {job_id} — status: complete")

        except Exception as exc:
            logger.exception(f"[pipeline] Job {job_id} failed: {exc}")
            async with AsyncSessionLocal() as err_db:
                await update_job_status(err_db, job_id, JobStatus.failed, str(exc))
                await err_db.commit()