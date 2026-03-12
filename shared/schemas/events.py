"""Kafka event schemas — Pydantic models for inter-service events."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DiseaseDetectedEvent(BaseModel):
    """Published by Disease Detection when an image is analyzed."""
    event: str = "disease.detected"
    upload_id: str
    farmer_id: str
    disease: str
    crop: str
    confidence: float
    location: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class AdvisoryReadyEvent(BaseModel):
    """Published by AI Advisory after generating treatment advice."""
    event: str = "advisory.ready"
    upload_id: str
    farmer_id: str
    disease: str
    crop: str
    advisory_id: str
    summary: str
    timestamp: datetime = None

    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class PriceAlertEvent(BaseModel):
    """Published by Market Price when a price threshold is crossed."""
    event: str = "price.alert"
    crop: str
    state: str
    mandi: str
    current_price: float
    threshold_price: float
    direction: str  # "above" or "below"
    timestamp: datetime = None

    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class IrrigationReminderEvent(BaseModel):
    """Published by Irrigation service for scheduled reminders."""
    event: str = "irrigation.reminder"
    farm_id: str
    farmer_id: str
    crop: str
    water_qty_liters: float
    message: str
    timestamp: datetime = None

    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)
