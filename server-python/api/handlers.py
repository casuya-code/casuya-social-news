"""Exception handlers that convert APIError into the standard response envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.errors import APIError
from config.logging_config import get_logger
from middleware.request_id import CONTEXT_HEADER, get_request_id

_logger = get_logger("api.errors")


def _envelope(request: Request, status: int, message: str, error_code: str) -> JSONResponse:
    request_id = get_request_id() or request.headers.get(CONTEXT_HEADER, "")
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "status_code": status,
            "message": message,
            "error_code": error_code,
            "request_id": request_id,
            "data": None,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach APIError handler (and a catch-all for unexpected failures)."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        _logger.error(
            "api_error",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
        )
        return _envelope(request, exc.status_code, exc.message, exc.error_code)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        _logger.exception("unhandled_error", path=request.url.path)
        return _envelope(request, 500, "Internal server error", "E0000")
