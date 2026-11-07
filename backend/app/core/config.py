from typing import List, Union
from pathlib import Path
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # workspace root


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Campus Intelligence"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "prototype-insecure-secret-key-change-in-prod-xyz-2026-campus"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v

    # Database
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/smart_campus.db"

    @field_validator("DATABASE_URL", mode="before")
    def resolve_database_url(cls, v: str) -> str:
        if v.startswith("sqlite:///./"):
            relative_part = v.replace("sqlite:///./", "")
            return f"sqlite:///{PROJECT_ROOT / relative_part}"
        return v

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "120/minute"
    AUTH_RATE_LIMIT: str = "20/minute"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
