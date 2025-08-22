# Real-Time Order Processing System — Python Stack (FastAPI)

Event-driven microservices for an e-commerce-style order workflow:
order placement → inventory check → payment → shipping → notifications.

**Stack**
- FastAPI (REST), Uvicorn (ASGI)
- Kafka via `aiokafka`
- Postgres via SQLAlchemy 2.0 + Psycopg 3
- Redis via `redis`
- JWT via `pyjwt` (HS256 demo secret) + role-based access
- Circuit breaker via `pybreaker` (Order → Payment health)
- API Gateway as a lightweight FastAPI reverse-proxy
- Docker Compose & Kubernetes (manifests included)
- CI via GitHub Actions

> For simplicity, JWT uses HS256 with `JWT_SECRET`. Swap to JWKS/OIDC in prod.

## Services
- **api-gateway**: AuthN/AuthZ, reverse-proxy routes to services.
- **order-service**: `POST /api/orders` publishes `order.created`.
- **inventory-service**: Consumes `order.created`, checks Redis/db, publishes `inventory.reserved|rejected`.
- **payment-service**: Mock authorization, publishes `payment.authorized|declined`.
- **shipping-service**: Consumes payment events, publishes `shipping.updated`.
- **notification-service**: Consumes domain events and logs "emails".

## Quick Start (Docker Compose)
```bash
docker compose up -d --build

# Create a demo JWT (do this on your machine):
python - <<'PY'
import jwt, time
print(jwt.encode({
  "sub":"customer1","roles":["customer"],"aud":"orders-api","iss":"orders-demo","iat":int(time.time())
}, "devsecret", algorithm="HS256"))
PY

# Create an order
TOKEN=<paste-token>
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '\''{"customerId":"c-1","items":[{"sku":"SKU-1","qty":2}]}'\'' \
  http://localhost:8080/api/orders
Kafka Topics
order.created

inventory.reserved | inventory.rejected

payment.authorized | payment.declined

shipping.updated

notification.send

Kubernetes (Minikube)
bash
Copy code
minikube start
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/infra/
kubectl apply -f k8s/services/
kubectl apply -f k8s/hpa/
kubectl -n orders port-forward svc/api-gateway 8080:80
ADRs & Docs
docs/adr/ADR-001-choose-kafka.md

Architecture diagram: docs/architecture.mmd (Mermaid)

Postman: docs/postman/collection.json
