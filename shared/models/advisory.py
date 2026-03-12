"""Advisory model — AI-generated treatment advice linked to an upload."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=False, unique=True, index=True)
    treatment = Column(Text, nullable=False)
    organic_alternative = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)
    fertilizer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Advisory for upload {self.upload_id}>"
