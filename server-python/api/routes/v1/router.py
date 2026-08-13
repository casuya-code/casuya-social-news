"""HTTP route definitions for the /api/v1 surface."""

from fastapi import APIRouter

from api.routes.v1 import health, news_routes, script_routes

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(script_routes.router, prefix="/scripts", tags=["scripts"])
api_v1_router.include_router(news_routes.router, prefix="/news", tags=["news"])
