"""Irrigation log model — historical irrigation recommendations."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class IrrigationLog(Base):
    __tablename__ = "irrigation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False, index=True)
    crop = Column(String(50), nullable=False)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    water_qty_liters_per_hectare = Column(Float, nullable=False)
    frequency = Column(String(30), nullable=False)
    recommended_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IrrigationLog {self.crop} — {self.water_qty_liters_per_hectare}L/ha>"
