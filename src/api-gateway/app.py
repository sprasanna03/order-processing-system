import os
from fastapi import FastAPI, Request, Response, Depends
import httpx
from auth import get_principal

ROUTES = {
    "/api/orders": ("http://order-service:8081", True),
    "/api/inventory": ("http://inventory-service:8082", True),
    "/api/payments": ("http://payment-service:8083", True),
    "/api/shipping": ("http://shipping-service:8084", True),
    "/api/notifications": ("http://notification-service:8085", True),
}

app = FastAPI(title="API Gateway")


@app.get("/actuator/health")
def health():
    return {"status": "UP"}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(full_path: str, request: Request, principal=Depends(get_principal)):
    path = "/" + full_path
    target_base = None
    for prefix, (url, _auth) in ROUTES.items():
        if path.startswith(prefix):
            target_base = url
            break
    if not target_base:
        return Response(status_code=404)

    async with httpx.AsyncClient() as client:
        target = f"{target_base}{path}"
        body = await request.body()
        resp = await client.request(
            request.method,
            target,
            content=body,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
