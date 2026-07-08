from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.rate_limit import limiter
from app.core.config import settings
from app.routers.ask import router as ask_router
from app.routers.auth import router as auth_router
from app.routers.f1 import f1_router
from app.routers.stat_of_day import router as stat_of_day_router
from app.routers.users import router as users_router


# Refuse to boot in a non-development environment with the known dev
# JWT signing key — otherwise a misconfigured deploy would silently
# sign tokens with a value an attacker can guess.
_DEV_SECRET_MARKERS = ("dev-secret-key-change-in-production",)
if settings.ENVIRONMENT != "development" and any(
    marker in settings.SECRET_KEY for marker in _DEV_SECRET_MARKERS
):
    raise RuntimeError(
        "SECRET_KEY is still the dev default while ENVIRONMENT is "
        f"{settings.ENVIRONMENT!r}. Set a strong, random SECRET_KEY before boot."
    )


app = FastAPI(
    title="Sportsona API",
    description="Sports aggregator platform API",
    version="0.1.0",
    servers=[{"url": settings.API_BASE_URL}] if settings.API_BASE_URL else None,
)

# Rate limiting (slowapi reads `app.state.limiter` and uses the registered
# exception handler to convert RateLimitExceeded → HTTP 429).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend. Auth is via Authorization header (bearer tokens
# returned in the response body, not cookies), so allow_credentials must stay
# False — keeping it True would block `allow_origins=["*"]` later and exposes
# us to credentialed cross-origin requests if anything ever sets a cookie.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(f1_router)
app.include_router(ask_router)
app.include_router(stat_of_day_router)

@app.get("/")
def root():
    return {"message": "Sportsona API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
