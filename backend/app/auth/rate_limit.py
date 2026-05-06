"""Shared SlowAPI Limiter instance for rate-limited auth endpoints.

Keeps the limiter in one place so multiple routers can decorate routes with
the same instance. Storage defaults to in-memory — fine for a single
backend replica. Swap to Redis-backed storage when scaling horizontally.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)
