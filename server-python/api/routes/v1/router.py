"""HTTP route definitions for the /api/v1 surface."""

from fastapi import APIRouter

from api.routes.v1 import (
    auth_routes,
    economy_routes,
    health,
    maintenance_routes,
    news_routes,
    script_routes,
    weather_routes,
)
from api.websocket_server import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(script_routes.router, prefix="/scripts", tags=["scripts"])
api_v1_router.include_router(news_routes.router, prefix="/news", tags=["news"])
api_v1_router.include_router(economy_routes.router, prefix="/economy", tags=["economy"])
api_v1_router.include_router(weather_routes.router, prefix="/weather", tags=["weather"])
api_v1_router.include_router(maintenance_routes.router, prefix="/maintenance", tags=["maintenance"])
api_v1_router.include_router(ws_router, tags=["realtime"])
