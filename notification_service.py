import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DISEASE_TOPIC = os.getenv("DISEASE_TOPIC", "disease.events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "notification-service-group")


class DiseaseEvent(BaseModel):
    pred_id: str
    healthy: str


class NotificationConsumer:
    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None

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

    async def consume(self) -> None:
        await self.start()
        try:
            if not self.consumer:
                raise RuntimeError("Consumer failed to initialize")

            async for msg in self.consumer:
                event = DiseaseEvent(**msg.value)
                print(
                    f"Prediction detail -> pred_id: {event.pred_id}, healthy: {event.healthy}",
                    flush=True,
                )
        finally:
            await self.stop()


if __name__ == "__main__":
    asyncio.run(NotificationConsumer().consume())
