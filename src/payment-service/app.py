import os
import asyncio
import random
from fastapi import FastAPI, Depends
from auth import get_principal
from kafka_util import get_consumer, get_producer
from db import healthcheck

INV_RESERVED = os.getenv("TOPIC_INV_RESERVED", "inventory.reserved")
PAY_AUTH = os.getenv("TOPIC_PAY_AUTH", "payment.authorized")
PAY_DECL = os.getenv("TOPIC_PAY_DECL", "payment.declined")

app = FastAPI(title="payment-service")


@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_inventory_reserved())


@app.get("/actuator/health")
def health():
    healthcheck()
    return {"status": "UP"}


@app.get("/api/payments/health")
def pay_health(principal=Depends(get_principal)):
    return {"status": "ok"}


async def consume_inventory_reserved():
    cons = await get_consumer(INV_RESERVED, group_id="payment-service")
    prod = await get_producer()
    try:
        async for msg in cons:
            order = msg.value.get("order")
            if random.random() < 0.9:
                await prod.send_and_wait(PAY_AUTH, {"order": order, "authCode": "OK123"})
            else:
                await prod.send_and_wait(PAY_DECL, {"order": order, "reason": "card_declined"})
    finally:
        await cons.stop()
        await prod.stop()
    