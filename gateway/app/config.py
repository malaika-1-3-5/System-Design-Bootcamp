"""Gateway-specific configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class GatewaySettings(BaseSettings):
    # Service URLs
    DISEASE_DETECTION_URL: str = "http://disease-detection:8001"
    AI_ADVISORY_URL: str = "http://ai-advisory:8002"
    IRRIGATION_URL: str = "http://irrigation:8003"
    MARKET_PRICE_URL: str = "http://market-price:8004"
    NOTIFICATION_URL: str = "http://notification:8005"

    # JWT
    JWT_SECRET_KEY: str = "super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 100

    # Database
    DATABASE_URL: str = "postgresql://agentchiguru:agentchiguru123@postgres:5432/agentchiguru_db"

    class Config:
        env_file = ".env"


@lru_cache()
def get_gateway_settings() -> GatewaySettings:
    return GatewaySettings()
