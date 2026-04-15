import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models.models import Job, JobStatus
from backend.schemas.jobs import JobCreate


async def get_existing_completed_job(
    db: AsyncSession, ticker: str, quarter: str, year: int
) -> Job | None:
    result = await db.execute(
        select(Job).where(
            Job.ticker == ticker,
            Job.quarter == quarter,
            Job.year == year,
            Job.status == JobStatus.complete,
        )
    )
    return result.scalar_one_or_none()


async def create_job(db: AsyncSession, user_id: uuid.UUID, data: JobCreate) -> Job:
    job = Job(
        user_id=user_id,
        ticker=data.ticker,
        quarter=data.quarter,
        year=data.year,
        status=JobStatus.pending,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def get_job_with_results(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(
            selectinload(Job.segments).selectinload("sentiment"),
            selectinload(Job.segments).selectinload("confidence"),
            selectinload(Job.segments).selectinload("entities"),
            selectinload(Job.segments).selectinload("summary"),
            selectinload(Job.price_data),
        )
    )
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    status: JobStatus,
    error_message: str | None = None,
) -> Job | None:
    job = await get_job_by_id(db, job_id)
    if not job:
        return None
    job.status = status
    if error_message is not None:
        job.error_message = error_message
    await db.flush()
    return job


async def set_transcript_text(
    db: AsyncSession, job_id: uuid.UUID, text: str
) -> Job | None:
    job = await get_job_by_id(db, job_id)
    if not job:
        return None
    # In Phase 1 we store inline. In Phase 2 this writes to GCS.
    job.transcript_gcs_path = f"inline:{job_id}"
    job.status = JobStatus.processing
    await db.flush()
    return job


async def list_jobs_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Job]:
    result = await db.execute(
        select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
    )
    return list(result.scalars().all())
