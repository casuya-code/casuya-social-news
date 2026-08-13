"""HTTP route definitions for the /api/v1 surface."""

from fastapi import APIRouter

from api.routes.v1 import health, script_routes

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(script_routes.router, prefix="/scripts", tags=["scripts"])
