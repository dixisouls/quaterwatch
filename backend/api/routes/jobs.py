import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.models import User, JobStatus
from backend.schemas.jobs import (
    JobCreate, JobStatusResponse, TranscriptUpload,
    JobResults, JobListItem
)
from backend.services import job_service, tasks_service
from backend.api.middleware.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for existing completed job
    existing = await job_service.get_existing_completed_job(
        db, data.ticker, data.quarter, data.year
    )
    if existing:
        return JobStatusResponse.model_validate(existing)

    # Create new job
    job = await job_service.create_job(db, current_user.id, data)

    # Enqueue to Cloud Tasks
    queued = await tasks_service.enqueue_job(job.id)
    if not queued:
        await job_service.update_job_status(db, job.id, JobStatus.failed,
            "Service temporarily unavailable, please try again in a moment.")
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable, please try again in a moment.",
        )

    await db.commit()
    await db.refresh(job)
    return JobStatusResponse.model_validate(job)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusResponse.model_validate(job)


@router.put("/{job_id}/transcript", response_model=JobStatusResponse)
async def upload_transcript(
    job_id: uuid.UUID,
    data: TranscriptUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.awaiting_upload:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is not awaiting a transcript upload (current status: {job.status})",
        )
    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcript text cannot be empty",
        )

    job = await job_service.set_transcript_text(db, job_id, data.text)
    await db.commit()
    await db.refresh(job)
    return JobStatusResponse.model_validate(job)


@router.get("/{job_id}/results", response_model=JobResults)
async def get_job_results(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await job_service.get_job_with_results(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.complete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is not complete yet (current status: {job.status})",
        )
    return JobResults.model_validate(job)


@router.get("", response_model=list[JobListItem])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = await job_service.list_jobs_for_user(db, current_user.id)
    return [JobListItem.model_validate(j) for j in jobs]
