from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Nyayrithm"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Two stores, split by data shape (see app/db/factory.py):
    #   PostgreSQL - firms, users, plans, cases, simulations, agents, the audit chain
    #   MongoDB    - turns, extracted evidence text, LLM usage events
    # DATABASE_URL may be sqlite+aiosqlite:/// for tests only.
    DATABASE_URL: str = "postgresql+asyncpg://nyayrithm:devpassword@localhost:5432/nyayrithm"
    MONGODB_URI: str = "mongodb://nyayrithm:devpassword@localhost:27017/?authSource=admin"
    MONGODB_DB: str = "nyayrithm"

    # Vector store: qdrant
    VECTOR_DB_BACKEND: Literal["qdrant"] = "qdrant"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # File storage backend: local | s3 | minio
    STORAGE_BACKEND: Literal["local", "s3", "minio"] = "local"
    STORAGE_LOCAL_ROOT: str = "./storage"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "nyayrithm-evidence"
    S3_ENDPOINT_URL: str | None = None  # for MinIO local

    MAX_UPLOAD_MB: int = 100

    # Task queue
    TASK_QUEUE_BACKEND: str = "celery+redis"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Cache
    CACHE_BACKEND: str = "redis"
    REDIS_URL: str = "redis://localhost:6379/2"

    # LLM Providers
    LLM_DEFAULT_PROVIDER: Literal["openai", "anthropic", "gemini", "ollama"] = "openai"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # local models; no API key

    # Embedder backend: openai | gemini | sentence-transformers | local
    EMBEDDER_BACKEND: Literal["openai", "gemini", "sentence-transformers", "local"] = "openai"
    EMBEDDING_DIMENSION: int = 1536  # openai text-embedding-3-small

    # Auth — bearer tokens are issued by Keycloak and verified here against its JWKS.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day (legacy local tokens)
    ALGORITHM: str = "HS256"
    # Server-side Keycloak URL (Docker: http://keycloak:8080). Used to fetch the JWKS.
    KEYCLOAK_URL: str = "http://localhost:8080"
    # Browser-facing URL; tokens may carry either host as their issuer.
    NEXT_PUBLIC_KEYCLOAK_URL: str = "http://localhost:8080"
    NEXT_PUBLIC_KEYCLOAK_REALM: str = "nyayrithm"
    # Extra accepted issuers (comma separated). The two derived from the URLs above
    # are always accepted.
    KEYCLOAK_EXTRA_ISSUERS: str = ""
    AUTH_JWKS_CACHE_SECONDS: int = 3600
    # Master-realm admin account the platform-admin portal uses to enable/disable users and
    # grant roles through Keycloak's admin REST API. Server-side only.
    KEYCLOAK_ADMIN_USER: str = ""
    KEYCLOAK_ADMIN_PASS: str = ""
    # Development authentication. Never available in production (validated below).
    #   off          normal: every request needs a valid Keycloak token
    #   open         token-less requests act as the seeded dev user (no login in either portal)
    #   credentials  real Keycloak login with the static accounts in keycloak/realm-dev.json
    DEV_AUTH_MODE: Literal["off", "open", "credentials"] = "off"
    AUTH_DEV_BYPASS: bool = False  # legacy switch; equivalent to DEV_AUTH_MODE=open
    # The seeded dev firm owner (matches keycloak/realm-dev.json).
    DEV_USER_ID: str = "00000000-0000-4000-8000-0000000000b1"
    # Seed "Dev Firm", plans and a sample case at startup (idempotent). Development only.
    SEED_DEV_DATA: bool = False

    # Public URL of the firm portal (used in invite links) and outgoing email.
    APP_URL: str = "http://localhost:3000"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@nyayrithm.local"

    # Legal accuracy. Extra jurisdiction packs (JSON, same schema as app/legal/packs) are
    # loaded from LEGAL_PACKS_DIR in addition to the bundled ones.
    LEGAL_PACKS_DIR: str | None = None
    LEGAL_REVIEW_ENABLED: bool = True

    # Simulation pacing — seconds to wait between turns. Keeps the turn loop
    # under free-tier LLM rate limits (Gemini flash free tier is ~10 RPM).
    SIMULATION_TURN_DELAY_SECONDS: float = 7.0

    @model_validator(mode="after")
    def _forbid_insecure_production(self) -> Settings:
        if self.APP_ENV == "production":
            if self.auth_bypass or self.DEV_AUTH_MODE != "off":
                raise ValueError("Dev authentication must not be enabled when APP_ENV=production")
            if self.SEED_DEV_DATA:
                raise ValueError("SEED_DEV_DATA must not be enabled when APP_ENV=production")
            if self.SECRET_KEY == "change-me-in-production":
                raise ValueError("SECRET_KEY must be set when APP_ENV=production")
        return self

    @property
    def auth_bypass(self) -> bool:
        """True when token-less requests are allowed to act as the dev user."""
        return self.AUTH_DEV_BYPASS or self.DEV_AUTH_MODE == "open"

    @property
    def keycloak_realm_path(self) -> str:
        return f"/realms/{self.NEXT_PUBLIC_KEYCLOAK_REALM}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.KEYCLOAK_URL.rstrip('/')}{self.keycloak_realm_path}/protocol/openid-connect/certs"

    @property
    def keycloak_issuers(self) -> set[str]:
        issuers = {
            f"{self.KEYCLOAK_URL.rstrip('/')}{self.keycloak_realm_path}",
            f"{self.NEXT_PUBLIC_KEYCLOAK_URL.rstrip('/')}{self.keycloak_realm_path}",
        }
        issuers.update(i.strip() for i in self.KEYCLOAK_EXTRA_ISSUERS.split(",") if i.strip())
        return issuers

    def get_api_key(self, provider: str) -> str | None:
        return {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }.get(provider)


@lru_cache
def get_settings() -> Settings:
    return Settings()
