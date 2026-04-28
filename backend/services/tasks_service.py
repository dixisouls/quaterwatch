import json
import uuid
from backend.config import get_settings

settings = get_settings()


async def enqueue_job(job_id: uuid.UUID) -> bool:
    try:
        if settings.cloud_tasks_emulator_host:
            return await _enqueue_via_emulator(job_id)
        else:
            return await _enqueue_via_gcp(job_id)
    except Exception as exc:
        print(f"[tasks] Failed to enqueue job {job_id}: {exc}")
        return False


async def _enqueue_via_emulator(job_id: uuid.UUID) -> bool:
    import grpc
    from google.cloud import tasks_v2

    emulator_host = settings.cloud_tasks_emulator_host

    channel = grpc.insecure_channel(emulator_host)

    transport = tasks_v2.services.cloud_tasks.transports.CloudTasksGrpcTransport(
        channel=channel,
    )

    client = tasks_v2.CloudTasksClient(transport=transport)

    parent = client.queue_path(
        settings.gcp_project_id,
        settings.gcp_location,
        settings.cloud_tasks_queue,
    )

    payload = json.dumps({"job_id": str(job_id)}).encode("utf-8")

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": "http://worker:8001/process",
            "headers": {"Content-Type": "application/json"},
            "body": payload,
        }
    }

    client.create_task(request={"parent": parent, "task": task})
    print(f"[tasks] Enqueued job {job_id} via emulator")
    return True


async def _enqueue_via_gcp(job_id: uuid.UUID) -> bool:
    from google.cloud import tasks_v2

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(
        settings.gcp_project_id,
        settings.gcp_location,
        settings.cloud_tasks_queue,
    )

    payload = json.dumps({"job_id": str(job_id)}).encode("utf-8")

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": "http://worker:8001/process",
            "headers": {"Content-Type": "application/json"},
            "body": payload,
        }
    }

    client.create_task(request={"parent": parent, "task": task})
    print(f"[tasks] Enqueued job {job_id} via GCP")
    return True