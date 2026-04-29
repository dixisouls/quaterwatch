from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Cloud Tasks
    cloud_tasks_emulator_host: str = ""
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    cloud_tasks_queue: str = "quarterwatch-jobs"

    # Cloud Storage
    gcs_bucket_name: str = "quarterwatch-transcripts"

    # Google Cloud
    google_genai_use_vertexai: bool = True
    google_cloud_project: str = ""
    google_cloud_location: str = "global"

    # External APIs
    fmp_api_key: str = ""
    alpha_vantage_api_key: str = ""

    # CORS
    frontend_url: str = "http://localhost:3000"
    worker_url: str = "http://localhost:8001"

    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
