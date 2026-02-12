from fastapi import APIRouter

from app.routers.f1.seasons import router as seasons_router
from app.routers.f1.drivers import router as drivers_router
from app.routers.f1.constructors import router as constructors_router
from app.routers.f1.races import router as races_router
from app.routers.f1.circuits import router as circuits_router

f1_router = APIRouter(prefix="/api/v1/f1", tags=["F1"])

f1_router.include_router(seasons_router)
f1_router.include_router(drivers_router)
f1_router.include_router(constructors_router)
f1_router.include_router(races_router)
f1_router.include_router(circuits_router)
