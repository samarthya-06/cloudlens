from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[2] / ".env", extra="ignore")
    aws_region: str = "ap-south-1"
    ai_provider: Literal["gemini"] = "gemini"
    gemini_api_key: str = ""
    gemini_model_id: str = "gemini-3.5-flash-lite"
    embedding_model_id: str = "gemini-embedding-001"
    embedding_dimensions: Literal[256, 512, 768, 1024, 3072] = 768
    aws_profile: str | None = None
    database_path: Path = Path("../runtime/cloudlens.sqlite")
    index_path: Path = Path("../runtime/index")
    artifact_path: Path = Path("../runtime/artifacts")
    s3_bucket: str = ""
    s3_prefix: str = "cloudlens/"
    demo_password: str = ""
    session_secret: str = ""
    cookie_secure: bool = False
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = 262144
    max_model_calls: int = 120
    model_timeout_seconds: int = 30
    investigation_timeout_seconds: int = 120
    max_session_analyses: int = 20
    queue_size: int = 4

    @field_validator("embedding_dimensions", mode="before")
    @classmethod
    def coerce_dimensions(cls, value):
        return int(value)

    @property
    def origins(self) -> set[str]:
        return set(self.allowed_origins.split(","))

    @property
    def generation_model(self) -> str:
        return self.gemini_model_id

    @property
    def inference_location(self) -> str:
        return "Google Gemini Developer API"
