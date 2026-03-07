"""
Simple Kafka Consumer Utility
"""

import asyncio
import json

from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
from ingestion import Event
from irrigation_service import IrrigationService

from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
TOPIC_NAME = "sensor.events"
CONSUMER_GROUP = "sensor_data_group"


class KafkaEventConsumer:
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=self.bootstrap_servers,
            group_id=CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    def store_event(self, event: Event):
        Base = declarative_base()
        class EventModel(Base):
            __tablename__ = "events"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            sensor_id= Column(String(100), nullable=False)
            temperature= Column(Float, nullable=False)
   
        engine = create_engine("postgresql://agriadmin:agriadmin123@db_service:5432/events")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            event_row = EventModel(sensor_id=event.sensor_id, temperature=event.temperature)
            db.add(event_row)
            db.commit()
            db.refresh(event_row)
            print(
                f"Event stored in database: {event_row.id} | {event_row.sensor_id} -> {event_row.temperature}",
                flush=True,
            )
            return event_row
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    
    async def process_events(self):
        consumer = KafkaEventConsumer()
        await consumer.start()
        try:
            async for msg in consumer.consumer:
                event = Event(**msg.value)
                self.store_event(event)
                irrigation_service = IrrigationService()
                irrigation_service.create_irrigation_data(event)

        finally:
            await consumer.stop()



if __name__ == "__main__":
    asyncio.run(KafkaEventConsumer().process_events())
    #async def consume(self):
        #async for msg in self.consumer:
            #event = Event(**msg.value)
            #print(f"   {event.sensor_id} → {event.temperature}")