"""Upload model — crop image uploads with disease detection results."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=True, index=True)
    image_path = Column(String(500), nullable=False)
    disease_detected = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    crop = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Upload {self.id} — {self.disease_detected}>"
