import os
import asyncio
from fastapi import FastAPI, Depends
from auth import get_principal
from kafka_util import get_consumer
from db import healthcheck
from loguru import logger

TOPICS = [
    os.getenv("TOPIC_ORDER_CREATED", "order.created"),
    os.getenv("TOPIC_INV_RESERVED", "inventory.reserved"),
    os.getenv("TOPIC_INV_REJECTED", "inventory.rejected"),
    os.getenv("TOPIC_PAY_AUTH", "payment.authorized"),
    os.getenv("TOPIC_PAY_DECL", "payment.declined"),
    os.getenv("TOPIC_SHIP_UPDATED", "shipping.updated"),
]

app = FastAPI(title="notification-service")


@app.on_event("startup")
async def startup():
    for t in TOPICS:
        asyncio.create_task(consume_topic(t))


@app.get("/actuator/health")
def health():
    healthcheck()
    return {"status": "UP"}


@app.get("/api/notifications/health")
def notif_health(principal=Depends(get_principal)):
    return {"status": "ok"}


async def consume_topic(topic: str):
    cons = await get_consumer(topic, group_id="notification-service")
    try:
        async for msg in cons:
            logger.info(f"Notify: topic={topic} payload={msg.value}")
    finally:
        await cons.stop()
