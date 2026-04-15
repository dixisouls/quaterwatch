import json
import uuid
from google.cloud import tasks_v2
from google.protobuf import duration_pb2
from backend.config import get_settings

settings = get_settings()


def get_tasks_client() -> tasks_v2.CloudTasksClient:
    """
    Returns a Cloud Tasks client pointed at the local emulator if
    CLOUD_TASKS_EMULATOR_HOST is set, otherwise uses real GCP credentials.
    """
    if settings.cloud_tasks_emulator_host:
        import os
        os.environ["CLOUD_TASKS_EMULATOR_HOST"] = settings.cloud_tasks_emulator_host

    return tasks_v2.CloudTasksClient()


def get_queue_path(client: tasks_v2.CloudTasksClient) -> str:
    return client.queue_path(
        settings.gcp_project_id,
        settings.gcp_location,
        settings.cloud_tasks_queue,
    )


async def enqueue_job(job_id: uuid.UUID) -> bool:
    """
    Enqueues a processing task for the given job_id.
    Returns True on success, False on failure.
    """
    try:
        client = get_tasks_client()
        parent = get_queue_path(client)

        payload = json.dumps({"job_id": str(job_id)}).encode("utf-8")

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"http://worker:8001/process",
                "headers": {"Content-Type": "application/json"},
                "body": payload,
            }
        }

        client.create_task(request={"parent": parent, "task": task})
        return True

    except Exception as exc:
        print(f"[tasks] Failed to enqueue job {job_id}: {exc}")
        return False
