"""FastAPI Users setup — UserManager, schemas, auth backend."""

import uuid
from typing import Optional, AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User, UserRole
from app.db import get_async_session
from app.config import get_gateway_settings

settings = get_gateway_settings()
SECRET = settings.JWT_SECRET_KEY


# ── Pydantic schemas ───────────────────────────────────────────────────────

class UserRead(schemas.BaseUser[uuid.UUID]):
    name: str
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    role: UserRole = UserRole.FARMER


class UserCreate(schemas.BaseUserCreate):
    name: str
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    role: UserRole = UserRole.FARMER


class UserUpdate(schemas.BaseUserUpdate):
    name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    role: Optional[UserRole] = None


# ── DB adapter ─────────────────────────────────────────────────────────────

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# ── User Manager ───────────────────────────────────────────────────────────

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# ── JWT auth backend ───────────────────────────────────────────────────────

bearer_transport = BearerTransport(tokenUrl="/api/v1/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=settings.JWT_EXPIRATION_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ── FastAPI Users instance ─────────────────────────────────────────────────

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
