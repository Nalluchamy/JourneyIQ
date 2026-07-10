import logging
import sys
from typing import Any

import structlog

from app.core.config import settings


def setup_logging() -> None:
    # Define shared processors for structlog
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Processor for final formatting based on environment
    formatter_processor: Any
    if settings.ENVIRONMENT.lower() == "production":
        formatter_processor = structlog.processors.JSONRenderer()
    else:
        formatter_processor = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog to work with standard logging
    structlog.configure(
        processors=[*shared_processors, formatter_processor],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Format handler for standard python logging (like uvicorn, alembic, etc.)
    # to output through structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=formatter_processor,
        foreign_pre_chain=shared_processors,
    ))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO if settings.ENVIRONMENT.lower() == "production" else logging.DEBUG)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


# Create a base logger
logger = structlog.get_logger("journeyiq")
