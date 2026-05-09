from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.rate_limit import limiter
from app.routers.auth import router as auth_router
from app.routers.f1 import f1_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Sportsona API",
    description="Sports aggregator platform API",
    version="0.1.0"
)

# Rate limiting (slowapi reads `app.state.limiter` and uses the registered
# exception handler to convert RateLimitExceeded → HTTP 429).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend.
# Includes the Vite default (5173) as a fallback so a dev who runs `vite --port 5173`
# explicitly still gets through during the transition.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(f1_router)

@app.get("/")
def root():
    return {"message": "Sportsona API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
