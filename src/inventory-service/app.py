import os
import asyncio
from fastapi import FastAPI, Depends
from auth import get_principal
from redis import Redis
from kafka_util import get_consumer, get_producer
from db import healthcheck

ORDER_CREATED = os.getenv("TOPIC_ORDER_CREATED", "order.created")
INV_RESERVED = os.getenv("TOPIC_INV_RESERVED", "inventory.reserved")
INV_REJECTED = os.getenv("TOPIC_INV_REJECTED", "inventory.rejected")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="inventory-service")
redis = Redis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("startup")
async def startup():
    redis.set("SKU-1", 10)
    asyncio.create_task(consume_orders())


@app.get("/actuator/health")
def health():
    healthcheck()
    return {"status": "UP"}


@app.get("/api/inventory/health")
def inv_health(principal=Depends(get_principal)):
    return {"redis": "ok"}


async def consume_orders():
    cons = await get_consumer(ORDER_CREATED, group_id="inventory-service")
    prod = await get_producer()
    try:
        async for msg in cons:
            order = msg.value
            ok = True
            for item in order.get("items", []):
                stock = int(redis.get(item["sku"]) or 0)
                if stock < item["qty"]:
                    ok = False
                    break
            if ok:
                for item in order.get("items", []):
                    redis.decrby(item["sku"], item["qty"])
                await prod.send_and_wait(INV_RESERVED, {"order": order})
            else:
                await prod.send_and_wait(INV_REJECTED, {"order": order, "reason": "out_of_stock"})
    finally:
        await cons.stop()
        await prod.stop()
