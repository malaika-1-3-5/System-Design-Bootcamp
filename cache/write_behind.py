from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime
import uuid
import json
import logging
import redis
import time


from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


from models import ProductCreate, ProductResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# 1. DATABASE SETUP (PostgreSQL)


DATABASE_URL = "postgresql://agentchiguru:agentchiguru123@localhost:5532/agentchiguru_db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products_write_behind"


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source": "redis_cache"
        }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# 2. REDIS SETUP (Cache)


REDIS_URL = "redis://localhost:6579/2"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


CACHE_TTL = 300  # 5 minutes
CACHE_PREFIX = "product_wb"


def cache_key(product_id: str) -> str:
    return f"{CACHE_PREFIX}:{product_id}"


def serialize_product(data: dict) -> str:
    return json.dumps(data)


def deserialize_product(data: str) -> dict:
    return json.loads(data)




# 3. BACKGROUND TASKS (The "Behind" part)
def sync_create_to_db(data: dict):
    time.sleep(2)  # Simulate delay
    db = SessionLocal()
    try:
        product = Product(
            id=uuid.UUID(data["id"]),
            name=data["name"],
            category=data["category"],
            price=data["price"],
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        db.add(product)
        db.commit()
        logger.info(f"Product with ID {data['id']} synced to DB.")
    except Exception as e:
        logger.error(f"Failed to sync product to DB: {e}")
    finally:
        db.close()

#4. The Fast API Application (The Behind part)


app = FastAPI(
    title="CRUD with Redis (Cache only)",
    description="Operations directly on Redis Key-Value Store"
)

@app.on_event("startup")
def startup():
    try:
        redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except redis.ConnectionError:
        logger.error(f"Failed to connect to Redis")

# --Create --

@app.post("/products/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, background_tasks: BackgroundTasks):
    # 1. Create product data
    product_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    product_data = {
        "id": product_id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "description": product.description,
        "created_at": now,
        "updated_at": now,
        "source": "redis_cache"
    }
    # 2. Cache in Redis
    try:
        redis_client.setex(
            cache_key(product_id),
            CACHE_TTL,
            serialize_product(product_data)
        )
        logger.info(f"Product created and cached with ID: {product_id}")
    except redis.ConnectionError:
        raise HTTPException(status_code=503,detail="Redis unavailable")
    background_tasks.add_task(sync_create_to_db, product_data)
    return product_data


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    key = cache_key(product_id)
    try:
        cached_product = redis_client.get(key)
        if cached_product:
            logger.info(f"Cache HIT: {product_id}")
            return deserialize_product(cached_product)
    except redis.ConnectionError:
        pass
    
    logger.info(f"Cache MISS: {product_id}")
    product = db.query(Product).filter(Product.id == uuid.UUID(product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        product_dict = product.to_dict()
        redis_client.setex(
            key,
            CACHE_TTL,
            serialize_product(product_dict)
        )
    except redis.ConnectionError:
        logger.error(f"Failed to cache product after DB fetch with ID: {product_id}")
    return product


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str):
    key = cache_key(product_id)
    try:
        if redis_client.delete(key) == 0:
            raise HTTPException(status_code=404, detail="Product not found in cache")
        logger.info(f"Product deleted from cache with ID: {product_id}")
    except redis.ConnectionError:
        raise HTTPException(status_code=503,detail="Redis unavailable")

    return None