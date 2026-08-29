from __future__ import annotations

from functools import lru_cache
from typing import Literal

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

    # Database backend: postgres | mongodb | sqlite | dynamodb
    DB_BACKEND: Literal["postgres", "mongodb", "sqlite", "dynamodb"] = "postgres"
    DATABASE_URL: str = "postgresql+asyncpg://nyayrithm:secret@localhost:5432/nyayrithm"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "nyayrithm"
    SQLITE_PATH: str = "./nyayrithm.db"
    DYNAMODB_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT_URL: str | None = None  # for local dev

    # Vector DB backend: qdrant | chroma | pinecone | weaviate | pgvector
    VECTOR_DB_BACKEND: Literal["qdrant", "chroma", "pinecone", "weaviate", "pgvector"] = "qdrant"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str | None = None

    # File storage backend: local | s3 | gcs | azure_blob | minio
    STORAGE_BACKEND: Literal["local", "s3", "gcs", "azure_blob", "minio"] = "local"
    STORAGE_LOCAL_ROOT: str = "./storage"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "nyayrithm-evidence"
    S3_ENDPOINT_URL: str | None = None  # for MinIO local

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
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Embedder backend: openai | cohere | gemini | sentence-transformers | local
    EMBEDDER_BACKEND: str = "openai"
    COHERE_API_KEY: str | None = None
    EMBEDDING_DIMENSION: int = 1536  # openai text-embedding-3-small

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # Simulation pacing — seconds to wait between turns. Keeps the turn loop
    # under free-tier LLM rate limits (Gemini flash free tier is ~10 RPM).
    SIMULATION_TURN_DELAY_SECONDS: float = 7.0

    def get_api_key(self, provider: str) -> str | None:
        return {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }.get(provider)


@lru_cache
def get_settings() -> Settings:
    return Settings()
