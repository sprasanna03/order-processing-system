import os
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from auth import require_role, get_principal
from kafka_util import get_producer
from db import healthcheck
import httpx
from pybreaker import CircuitBreaker

ORDER_CREATED = os.getenv("TOPIC_ORDER_CREATED", "order.created")
PAYMENT_HEALTH = os.getenv("PAYMENT_HEALTH_URL", "http://payment-service:8083/actuator/health")

breaker = CircuitBreaker(fail_max=3, reset_timeout=10)


class Item(BaseModel):
    sku: str
    qty: int = Field(gt=0)


class OrderRequest(BaseModel):
    customerId: str
    items: list[Item]


app = FastAPI(title="order-service")


@app.get("/actuator/health")
def health():
    healthcheck()
    return {"status": "UP"}


@app.post("/api/orders")
async def create_order(req: OrderRequest, principal=Depends(require_role("customer"))):
    payload = {"customerId": req.customerId, "items": [i.dict() for i in req.items]}
    producer = await get_producer()
    try:
        await producer.send_and_wait(ORDER_CREATED, payload)
    finally:
        await producer.stop()
    return {"status": "PUBLISHED", "event": "order.created"}


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, principal=Depends(get_principal)):
    return {"id": order_id, "status": "PENDING"}


@app.get("/api/orders/payment-health")
def payment_health():
    @breaker
    def call():
        r = httpx.get(PAYMENT_HEALTH, timeout=3.0)
        r.raise_for_status()
        return r.json()

    try:
        return call()
    except Exception:
        return {"status": "DEGRADED"}
