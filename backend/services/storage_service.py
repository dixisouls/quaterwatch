import asyncio
import logging
from google.cloud import storage
from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger("worker.storage")

def _get_client() -> storage.Client:
    return storage.Client()


async def upload_transcript(job_id: str, transcript: str) -> str | None:
    try:
        def _upload():
            client = _get_client()
            bucket = client.bucket(settings.gcs_bucket_name)
            blob_name = f"transcripts/{job_id}.txt"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(transcript, content_type="text/plain")
            return blob_name
        blob_name = await asyncio.to_thread(_upload)
        logger.info(f"[storage] Uploaded transcript for job {job_id} to {blob_name}")
        return blob_name
    except Exception as exc:
        logger.exception(f"[storage] Failed to upload transcript for job {job_id}: {exc}")
        return None


async def download_transcript(gcs_path: str) -> str | None:
    try:
        def _download():
            client = _get_client()
            bucket = client.bucket(settings.gcs_bucket_name)
            blob = bucket.blob(gcs_path)
            return blob.download_as_text()
        text = await asyncio.to_thread(_download)
        logger.info(f"[storage] Downloaded transcript from {gcs_path}")
        return text
    except Exception as exc:
        logger.exception(f"[storage] Failed to download transcript from {gcs_path}: {exc}")
        return None