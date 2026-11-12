import json
from pathlib import Path
from typing import List, Optional, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # repository root

_INSECURE_DEFAULT_SECRET = "dev-only-insecure-secret-change-me"
# Passwords that appear in the development templates and compose file; never valid in production.
_DEV_DATABASE_MARKERS = ("acedra-dev-password", "acedra-ci")


def _is_local(url: str) -> bool:
    return any(host in url for host in ("localhost", "127.0.0.1", "0.0.0.0"))


class Settings(BaseSettings):
    """All runtime configuration, read from environment variables (and backend/.env in development).

    Invalid combinations fail fast at import time; in production the API refuses to start with an insecure
    secret, wildcard CORS, SQLite or an incomplete SMTP setup.
    """

    PROJECT_NAME: str = "ACEDRA"
    VERSION: str = "1.0.0-rc.1"
    ENVIRONMENT: str = "development"  # development | test | production
    API_V1_PREFIX: str = "/api/v1"
    PUBLIC_APP_URL: str = "http://localhost:5173"

    # Security
    SECRET_KEY: str = _INSECURE_DEFAULT_SECRET
    ALLOW_INSECURE_DEV_SECRET: bool = False
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INVITATION_TTL_HOURS: int = 72
    PASSWORD_RESET_TTL_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 10
    # Consecutive failed sign-ins before an account is locked, and for how long.
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, str):
            return json.loads(v)
        return v

    # Database
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/acedra.db"
    # Read by docker/entrypoint.sh to load the sample universities. Declared here so production can refuse it.
    SEED_DEMO_DATA: bool = False
    AUTO_CREATE_SCHEMA: bool = True  # development convenience; production uses Alembic

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("sqlite:///./"):
            return f"sqlite:///{PROJECT_ROOT / v.replace('sqlite:///./', '')}"
        return v

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "240/minute"
    AUTH_RATE_LIMIT: str = "20/minute"
    ENQUIRY_RATE_LIMIT: str = "5/hour"
    CONTACT_RATE_LIMIT: str = "5/hour"
    # Where rate-limit counters live. "memory://" is per process; production with more than one worker or
    # instance must use a shared store, e.g. "redis://redis:6379/0".
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    # When true, workspace API calls are refused (HTTP 428) until the signed-in person has accepted the current
    # Terms and Privacy Policy. The web app always asks for acceptance before showing a workspace.
    LEGAL_ACCEPTANCE_ENFORCED: bool = False

    # Uploads
    MAX_UPLOAD_MB: int = 10

    # AI providers (all optional; ACEDRA is transparent when none is configured)
    LLM_PROVIDER: str = "none"  # none | openai_compatible | anthropic | ollama
    LLM_MODEL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT_SECONDS: int = 30

    EMBEDDING_PROVIDER: str = "lexical"  # lexical | openai_compatible | ollama
    EMBEDDING_MODEL: Optional[str] = None
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None

    # Email delivery
    EMAIL_PROVIDER: str = "log"  # log | smtp
    EMAIL_FROM: str = "ACEDRA <no-reply@acedra.local>"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_STARTTLS: bool = True
    EMAIL_MAX_ATTEMPTS: int = 5
    EMAIL_RETRY_INTERVAL_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def validate_environment(self):
        problems = []
        environment = self.ENVIRONMENT.lower()
        if environment not in {"development", "test", "production"}:
            problems.append(f"ENVIRONMENT must be development, test or production (got '{self.ENVIRONMENT}').")
        # Fail closed: the built-in secret is tolerated only on a developer's own SQLite database. Anything
        # pointed at a real database server must have its own secret, whatever ENVIRONMENT says.
        if not self.is_production and self.SECRET_KEY == _INSECURE_DEFAULT_SECRET \
                and not self.DATABASE_URL.startswith("sqlite") and environment != "test" \
                and not self.ALLOW_INSECURE_DEV_SECRET:
            problems.append("SECRET_KEY must be set when using a database server "
                            "(set ALLOW_INSECURE_DEV_SECRET=true only for a local throwaway stack).")
        if self.is_production:
            if self.SECRET_KEY == _INSECURE_DEFAULT_SECRET or len(self.SECRET_KEY) < 32 \
                    or len(set(self.SECRET_KEY)) < 10:
                problems.append("SECRET_KEY must be set to a random value of at least 32 characters.")
            if any(o == "*" for o in self.CORS_ORIGINS):
                problems.append("CORS_ORIGINS must list explicit origins in production.")
            if self.DATABASE_URL.startswith("sqlite"):
                problems.append("DATABASE_URL must point to PostgreSQL in production.")
            if self.EMAIL_PROVIDER != "smtp":
                problems.append("EMAIL_PROVIDER must be smtp in production: with 'log', invitations and "
                                "password resets are stored on the server and never delivered.")
            elif not self.SMTP_HOST:
                problems.append("SMTP_HOST is required when EMAIL_PROVIDER=smtp.")
            if "acedra.local" in self.EMAIL_FROM or "@" not in self.EMAIL_FROM:
                problems.append("EMAIL_FROM must be a real sender address on your own domain.")
            if any(marker in self.DATABASE_URL for marker in _DEV_DATABASE_MARKERS):
                problems.append("DATABASE_URL still uses a development password.")
            if any(_is_local(origin) for origin in self.CORS_ORIGINS) or _is_local(self.PUBLIC_APP_URL):
                problems.append("CORS_ORIGINS and PUBLIC_APP_URL must not point at localhost in production.")
            if self.SEED_DEMO_DATA:
                problems.append("SEED_DEMO_DATA must be false in production: the sample universities use "
                                "published demonstration passwords.")
            if self.ALLOW_INSECURE_DEV_SECRET:
                problems.append("ALLOW_INSECURE_DEV_SECRET must not be set in production.")
            if not self.PUBLIC_APP_URL.startswith("https://"):
                problems.append("PUBLIC_APP_URL must be an https:// address in production.")
            self.AUTO_CREATE_SCHEMA = False
        if self.LLM_PROVIDER not in {"none", "openai_compatible", "anthropic", "ollama"}:
            problems.append(f"Unsupported LLM_PROVIDER '{self.LLM_PROVIDER}'.")
        if self.EMBEDDING_PROVIDER not in {"lexical", "openai_compatible", "ollama"}:
            problems.append(f"Unsupported EMBEDDING_PROVIDER '{self.EMBEDDING_PROVIDER}'.")
        if self.EMAIL_PROVIDER not in {"log", "smtp"}:
            problems.append(f"Unsupported EMAIL_PROVIDER '{self.EMAIL_PROVIDER}'.")
        if problems:
            raise ValueError("Invalid ACEDRA configuration: " + " ".join(problems))
        return self


settings = Settings()

