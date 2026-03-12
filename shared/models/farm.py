"""Farm model — individual farm plots belonging to a farmer."""

import uuid
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    crop_type = Column(String(50), nullable=True)
    area_hectares = Column(Float, nullable=True)
    soil_type = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Farm {self.name} ({self.crop_type})>"
