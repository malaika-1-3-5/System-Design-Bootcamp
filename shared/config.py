"""Shared configuration for all Agent Chiguru AI services."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    # PostgreSQL
    POSTGRES_USER: str = "agentchiguru"
    POSTGRES_PASSWORD: str = "agentchiguru123"
    POSTGRES_DB: str = "agentchiguru_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://agentchiguru:agentchiguru123@localhost:5432/agentchiguru_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6433

    # LLM
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "mock"  # openai | ollama | mock
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # JWT
    JWT_SECRET_KEY: str = "super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Service URLs
    DISEASE_DETECTION_URL: str = "http://localhost:8001"
    AI_ADVISORY_URL: str = "http://localhost:8002"
    IRRIGATION_URL: str = "http://localhost:8003"
    MARKET_PRICE_URL: str = "http://localhost:8004"
    NOTIFICATION_URL: str = "http://localhost:8005"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
