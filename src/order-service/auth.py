import os
import typing as t
import time
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

bearer = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_AUD = os.getenv("JWT_AUDIENCE", "orders-api")
JWT_ISS = os.getenv("JWT_ISSUER", "orders-demo")


class Principal(t.TypedDict):
    sub: str
    roles: t.List[str]


def get_principal(token: HTTPAuthorizationCredentials = Depends(bearer)) -> Principal:
    if token is None:
        raise HTTPException(401, "Missing bearer token")
    try:
        payload = jwt.decode(
            token.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            audience=JWT_AUD,
            options={"require": ["aud"]},
        )
        now = int(time.time())
kubectl apply -f k8s/ -n orders        if "iss" in payload and payload["iss"] != JWT_ISS:
            raise Exception("bad issuer")
        roles = payload.get("roles", [])
        return {"sub": payload.get("sub", "?"), "roles": roles}
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")


def require_role(role: str):
    def dep(p: Principal = Depends(get_principal)):
        if role not in p["roles"]:
            raise HTTPException(403, "Forbidden")
        return p

    return dep
