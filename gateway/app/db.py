"""Async database session for FastAPI Users (gateway only)."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from shared.config import get_settings

settings = get_settings()

# Convert sync URL to async URL for asyncpg driver
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

async_engine = create_async_engine(async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_session():
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
