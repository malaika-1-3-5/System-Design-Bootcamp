from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    description: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None

class ProductResponse(BaseModel):
    id: uuid.UUID | str
    name: str
    category: str
    price: float
    description: Optional[str]
    created_at: datetime | str
    updated_at: datetime | str
    source: str = "database"

    class Config:
        from_attributes = True