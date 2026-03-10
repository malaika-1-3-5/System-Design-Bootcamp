import asyncio
import json
import os
from datetime import datetime

import requests
from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DISEASE_TOPIC = os.getenv("DISEASE_TOPIC", "disease.events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "disease-detection-group")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agriadmin:agriadmin123@db_service:5432/agri_db",
)
NOTIFIER_URL = os.getenv(
    "NOTIFIER_URL",
    "http://notification_service:8000/api/v1/notifications",
)

Base = declarative_base()


class DiseaseAlert(Base):
    __tablename__ = "disease_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(100), nullable=False)
    crop_type = Column(String(60), nullable=False)
    disease_name = Column(String(120), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    message = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PlantObservation(BaseModel):
    sensor_id: str
    crop_type: str
    leaf_moisture: float
    air_humidity: float
    leaf_temperature: float
    spot_count: int
    observed_at: str


def detect_disease(observation: PlantObservation) -> tuple[bool, str, str, float, str]:
    score = 0.0

    if observation.air_humidity >= 85:
        score += 0.25
    if observation.leaf_moisture >= 70:
        score += 0.25
    if 20 <= observation.leaf_temperature <= 30:
        score += 0.2
    if observation.spot_count >= 4:
        score += 0.3

    if score >= 0.7:
        severity = "high"
    elif score >= 0.5:
        severity = "medium"
    else:
        severity = "low"

    disease_detected = score >= 0.5
    disease_name = "Possible Leaf Spot" if disease_detected else "No disease"

    if disease_detected:
        message = (
            f"Potential disease detected for {observation.crop_type} at sensor "
            f"{observation.sensor_id} with {severity} severity"
        )
    else:
        message = (
            f"No disease pattern detected for {observation.crop_type} at "
            f"sensor {observation.sensor_id}"
        )

    return disease_detected, disease_name, severity, round(score, 2), message


class DiseaseDetectionWorker:
    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None
        self.engine = create_engine(DATABASE_URL)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    async def start(self) -> None:
        self.consumer = AIOKafkaConsumer(
            DISEASE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self.consumer.start()

    async def stop(self) -> None:
        if self.consumer:
            await self.consumer.stop()

    def save_alert(
        self,
        observation: PlantObservation,
        disease_name: str,
        severity: str,
        confidence: float,
        message: str,
    ) -> DiseaseAlert:
        db = self.session_local()
        try:
            alert = DiseaseAlert(
                sensor_id=observation.sensor_id,
                crop_type=observation.crop_type,
                disease_name=disease_name,
                severity=severity,
                confidence=confidence,
                message=message,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            return alert
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def notify(self, alert: DiseaseAlert) -> None:
        payload = {
            "sensor_id": alert.sensor_id,
            "crop_type": alert.crop_type,
            "disease_name": alert.disease_name,
            "severity": alert.severity,
            "confidence": alert.confidence,
            "message": alert.message,
            "created_at": alert.created_at.isoformat(),
        }
        try:
            requests.post(NOTIFIER_URL, json=payload, timeout=4)
        except requests.RequestException as exc:
            print(f"Notifier call failed: {exc}", flush=True)

    async def run(self) -> None:
        await self.start()
        try:
            if not self.consumer:
                raise RuntimeError("Consumer failed to initialize")

            async for message in self.consumer:
                observation = PlantObservation(**message.value)
                detected, disease_name, severity, confidence, note = detect_disease(observation)

                if not detected:
                    print(note, flush=True)
                    continue

                alert = self.save_alert(observation, disease_name, severity, confidence, note)
                self.notify(alert)
                print(
                    f"Alert saved and notification sent: sensor={alert.sensor_id}, severity={alert.severity}",
                    flush=True,
                )
        finally:
            await self.stop()


if __name__ == "__main__":
    asyncio.run(DiseaseDetectionWorker().run())
