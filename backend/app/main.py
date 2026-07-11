import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.api.api import api_router
from app.core.config import settings
from app.core.logging_config import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup tasks
    from app.services.ml.scheduler import start_scheduler, stop_scheduler
    setup_logging()
    logger.info(
        "Starting JourneyIQ Backend Service",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
    start_scheduler()
    yield
    # Shutdown tasks
    logger.info("Stopping JourneyIQ Backend Service")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="JourneyIQ - Personalized Customer Journey Optimization Platform API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.middleware.gzip import GZipMiddleware

from app.middleware.security import RequestTimeoutMiddleware, SecurityHeadersMiddleware

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTimeoutMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request ID Middleware
@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    clear_contextvars()

    # Check if request has Request-ID, generate if not
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # Inject request_id into state & logger context
    request.state.request_id = request_id
    bind_contextvars(
        request_id=request_id,
        endpoint=request.url.path,
        method=request.method,
    )

    start_time = time.time()

    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed with unhandled exception",
            method=request.method,
            path=request.url.path,
            duration_ms=round(process_time * 1000, 2),
            error=str(e),
        )
        # Re-raise so the exception handler will format the response
        raise e


# Centralized Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "Request validation failed", request_id=request_id, errors=exc.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "ValidationError",
            "message": "Invalid request body or parameters.",
            "request_id": request_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "HTTP exception occurred",
        request_id=request_id,
        status_code=exc.status_code,
        message=exc.detail,
    )

    # Handle dict details (used by our health check or standard sub-systems)
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,  # Keep the dict details unchanged
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTPException",
            "message": exc.detail,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "An unhandled exception escaped middleware",
        request_id=request_id,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": "An unexpected server error occurred.",
            "request_id": request_id,
        },
    )


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
