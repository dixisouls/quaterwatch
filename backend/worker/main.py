import uuid
import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager

from backend.database import engine
from backend.worker.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="QuarterWatch Worker", lifespan=lifespan)


@app.post("/process")
async def process_job(request: Request):
    body = await request.json()
    job_id_str = body.get("job_id")

    if not job_id_str:
        raise HTTPException(status_code=400, detail="Missing job_id")

    try:
        job_id = uuid.UUID(job_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    logger.info(f"[worker] Received job {job_id}")

    # Run pipeline in background so Cloud Tasks gets a fast 200 response
    asyncio.create_task(run_pipeline(job_id))

    return {"status": "accepted", "job_id": str(job_id)}


@app.get("/health")
async def health():
    return {"status": "ok"}
