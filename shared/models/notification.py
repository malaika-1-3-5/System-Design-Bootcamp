"""Notification model — alerts sent to farmers."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # disease_alert, advisory, price_alert, irrigation
    channel = Column(String(20), nullable=False, default="email")  # email, sms, in_app
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



    def __repr__(self):
        return f"<Notification {self.type} → {self.farmer_id} [{self.status}]>"
