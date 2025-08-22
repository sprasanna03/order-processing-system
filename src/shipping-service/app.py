import os
import asyncio
from fastapi import FastAPI, Depends
from auth import get_principal
from kafka_util import get_consumer, get_producer
from db import healthcheck

PAY_AUTH = os.getenv("TOPIC_PAY_AUTH", "payment.authorized")
SHIP_UPDATED = os.getenv("TOPIC_SHIP_UPDATED", "shipping.updated")

app = FastAPI(title="shipping-service")


@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_payments())


@app.get("/actuator/health")
def health():
    healthcheck()
    return {"status": "UP"}


@app.get("/api/shipping/health")
def ship_health(principal=Depends(get_principal)):
    return {"status": "ok"}


async def consume_payments():
    cons = await get_consumer(PAY_AUTH, group_id="shipping-service")
    prod = await get_producer()
    try:
        async for msg in cons:
            order = msg.value.get("order")
            shipment = {"tracking": "TRK-" + order["customerId"], "status": "CREATED"}
            await prod.send_and_wait(SHIP_UPDATED, {"order": order, "shipment": shipment})
    finally:
        await cons.stop()
        await prod.stop()
