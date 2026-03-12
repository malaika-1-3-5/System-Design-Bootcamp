"""Market price model — mandi price data for crops."""

import uuid
from datetime import date
from sqlalchemy import Column, String, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    mandi = Column(String(100), nullable=False)
    price_per_quintal = Column(Float, nullable=False)
    price_date = Column(Date, default=date.today)

    def __repr__(self):
        return f"<MarketPrice {self.crop} @ {self.mandi} — ₹{self.price_per_quintal}/q>"
