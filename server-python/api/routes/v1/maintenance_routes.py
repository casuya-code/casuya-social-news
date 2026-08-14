"""Maintenance endpoints: on-demand retention sweep.

POST /api/v1/maintenance/retention — run the full retention policy now
(audio dirs, DB article purge, script summary compression).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from config.logging_config import get_logger
from database.engine import SessionLocal
from maintenance.retention import run_retention
from security.api_key_auth import verify_api_key

_logger = get_logger("api.maintenance")

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/retention")
async def retention_sweep(dry_run: bool = False) -> dict:
    """Run the README retention policy now and report what would be/was cleaned."""
    try:
        session = SessionLocal()
    except Exception as exc:  # noqa: BLE001 - DB down → audio-only sweep
        _logger.warning("maintenance_db_unavailable", error=str(exc))
        session = None

    try:
        result = await run_retention(dry_run=dry_run, session=session)
        _logger.info("retention_sweep_complete", result=result)
        return result
    finally:
        if session is not None:
            try:
                await session.close()
            except Exception:  # noqa: BLE001
                pass
