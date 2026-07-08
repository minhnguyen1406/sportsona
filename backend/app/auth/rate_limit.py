"""Shared SlowAPI Limiter instance for rate-limited endpoints.

Keeps the limiter in one place so multiple routers can decorate routes with
the same instance. Storage defaults to in-memory — fine for a single
backend replica. Swap to Redis-backed storage when scaling horizontally.

Key strategy: authenticated requests are keyed by user id, anonymous ones
by client IP. Behind a proxy/CDN every client shares the proxy's IP, so
IP-only keys would let one user exhaust everyone's quota (and conversely,
let the proxy's whole user base be starved by one abuser). The token is
signature-verified before it becomes a key — an unverified header would
let attackers mint unlimited buckets with random strings.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.auth.security import decode_access_token


def user_or_ip(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if sub is not None:
                return f"user:{sub}"
        except Exception:
            # Invalid/expired token → fall through to the IP bucket. The
            # endpoint's own auth will reject it anyway; we just need a key.
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=user_or_ip)
