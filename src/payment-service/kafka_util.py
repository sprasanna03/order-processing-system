import os
import asyncio
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")


def json_serializer(v: dict) -> bytes:
    return json.dumps(v).encode("utf-8")


def json_deserializer(v: bytes) -> dict:
    return json.loads(v.decode("utf-8"))


async def get_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=json_serializer
    )
    await producer.start()
    return producer


async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=BOOTSTRAP,
        group_id=group_id,
        value_deserializer=json_deserializer,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    return consumer
