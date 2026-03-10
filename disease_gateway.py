import json
import os
import random
import shutil
import uuid

from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends, FastAPI, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DISEASE_TOPIC = os.getenv("DISEASE_TOPIC", "disease.events")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agriadmin:agriadmin123@db_service:5432/agri_db",
)
IMAGE_STORAGE_DIR = os.getenv("IMAGE_STORAGE_DIR", "/app/uploads")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Disease Detection Service")
api = APIRouter(prefix="/api/v1", tags=["disease-detection"])


class DiseasePrediction(Base):
    __tablename__ = "disease_prediction"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_path = Column(String(300), nullable=False)
    prediction_detail = Column(String(120), nullable=False)
    healthy = Column(Boolean, nullable=False)


class PredictionResponse(BaseModel):
    pred_id: str
    image_path: str
    prediction_detail: str
    healthy: bool


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self.producer.start()

    async def stop(self) -> None:
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, key: str, payload: dict) -> None:
        if not self.producer:
            raise RuntimeError("Producer not initialized")
        await self.producer.send_and_wait(topic=topic, key=key, value=payload)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@api.post("/disease/predict", response_model=PredictionResponse)
async def predict_disease(file: UploadFile = File(...), db: Session = Depends(get_db)):
    pred_id = uuid.uuid4()
    file_ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    file_name = f"{pred_id}{file_ext}"
    file_path = os.path.join(IMAGE_STORAGE_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    healthy = random.choice([True, False])
    prediction_detail = "No disease detected" if healthy else "Disease pattern detected"

    row = DiseasePrediction(
        id=pred_id,
        image_path=file_path,
        prediction_detail=prediction_detail,
        healthy=healthy,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    event = {
        "pred_id": str(row.id),
        "healthy": "yes" if row.healthy else "no",
    }

    publisher = KafkaPublisher(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await publisher.start()
    try:
        await publisher.publish(topic=DISEASE_TOPIC, key=str(row.id), payload=event)
    finally:
        await publisher.stop()

    return PredictionResponse(
        pred_id=str(row.id),
        image_path=row.image_path,
        prediction_detail=row.prediction_detail,
        healthy=row.healthy,
    )


@api.get("/health")
def health_check():
    return {"status": "ok", "service": "disease-detection-service"}


app.include_router(api)
