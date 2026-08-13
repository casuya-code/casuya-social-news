"""JSON-structured logging using structlog."""

import logging
import sys

import structlog

from config.settings import get_settings

_settings = get_settings()


def _add_request_id(logger, method_name, event_dict):
    """Attach request_id from thread-local if present (set by middleware)."""
    from middleware.request_id import get_request_id

    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def setup_logging() -> None:
    """Configure structlog for JSON output (or readable text in dev)."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        _add_request_id,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if _settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *shared_processors,
            renderer,
        ]
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(_settings.log_level)

    # Silence noisy third-party loggers in development.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
