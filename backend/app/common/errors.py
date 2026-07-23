"""Reusable OpenAPI response definitions for auth and rate-limit errors.

Pass via ``responses=`` on a router or endpoint so generated clients
(and the Swagger UI) know what to expect.
"""

UNAUTHORIZED = {
    401: {"description": "Missing or invalid credentials"},
}

RATE_LIMITED = {
    429: {"description": "Too many requests — rate limit exceeded"},
}
