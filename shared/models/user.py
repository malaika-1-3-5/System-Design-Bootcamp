"""User model — registered users of the platform.

Plain SQLAlchemy model with no fastapi_users dependency.
The gateway's fastapi_users setup works with this model via duck typing —
it only requires the standard columns to exist, not the base class.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class UserRole(str, enum.Enum):
    FARMER = "FARMER"
    AGENT  = "AGENT"
    ADMIN  = "ADMIN"


class User(Base):
    __tablename__ = "users"

    # ── FastAPI Users required columns ─────────────────────────────────────
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(320), unique=True, index=True, nullable=False)
    hashed_password = Column(String(1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    is_superuser    = Column(Boolean, default=False, nullable=False)
    is_verified     = Column(Boolean, default=False, nullable=False)

    # ── Custom fields ──────────────────────────────────────────────────────
    name       = Column(String(100), nullable=False)
    phone      = Column(String(15),  nullable=True)
    state      = Column(String(50),  nullable=True)
    district   = Column(String(50),  nullable=True)
    role       = Column(Enum(UserRole), nullable=False, default=UserRole.FARMER)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"
