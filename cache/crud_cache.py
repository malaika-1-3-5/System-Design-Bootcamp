from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json
import logging
import redis

from models import ProductCreate, ProductUpdate, ProductResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6579/1"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL = 300 #5 minutes
CACHE_PREFIX = "product_cache"

def cache_key(product_id: str) -> str:
    return f"{CACHE_PREFIX}:{product_id}"

def serialize_product(data: dict) -> str:
    """Serialize product dictionary to JSON string."""
    #Ensure dta is JSON serializable, especially datetime objects
    return json.dumps(data)

def deserialize_product(data: str) -> dict:
    """Deserialize JSON string back to product dictionary."""
    return json.loads(data)

app = FastAPI(
    title="CRUD with Redis (Cache Only)",
    description="Operations directly on Redis Key-Value store",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    logger.info("Starting CRUD Cache Service...")
    try:
        redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except redis.exceptions.ConnectionError as e:
        logger.warning("Redis unavailable")


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate):
    product_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    product_data = {
        "id": product_id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "description": product.description,
        "created_at": timestamp,
        "updated_at": timestamp,
        "source": "redis_cache"
    }

    try:
        redis_client.setex(
            cache_key(product_id),
            CACHE_TTL,
            serialize_product(product_data)
        )
        logger.info(f"Product created and cached with ID: {product_id}")
    
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    return product_data

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    try:
        cached = redis_client.get(cache_key(product_id))
        if cached:
            logger.info(f"Product retrieved from cache with ID: {product_id}")
            return deserialize_product(cached)
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found in cache")
