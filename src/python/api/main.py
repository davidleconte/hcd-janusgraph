"""
FastAPI Analytics Service
=========================

Slim app factory that wires routers, middleware, and error handlers.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.python.config.settings import Settings, get_settings

from .dependencies import close_graph_connection, limiter, verify_auth
from .models import ErrorResponse
from .routers import aml, fraud, health, ubo


def _configure_logging(settings: Settings) -> None:
    """Configure root logger; optionally emit JSON lines."""
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler()

    if settings.log_json:
        from pythonjsonlogger import jsonlogger

        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    handler.setFormatter(formatter)
    root.addHandler(handler)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    _configure_logging(settings)

    from src.python.utils.startup_validation import validate_startup

    result = validate_startup(strict=False)
    if result.has_errors:
        for issue in result.issues:
            logger.error("Startup validation: %s", issue.message)
        raise RuntimeError("Startup validation failed — check configuration")
    for issue in result.issues:
        logger.warning("Startup validation: %s", issue.message)

    from src.python.utils.tracing import TracingConfig, initialize_tracing

    tracing_config = TracingConfig(
        service_name="graph-analytics-api",
        enabled=settings.tracing_enabled,
    )
    tracing_mgr = initialize_tracing(tracing_config)

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        logger.debug("opentelemetry-instrumentation-fastapi not installed, skipping")

    logger.info("Starting Analytics API Service...")
    yield
    close_graph_connection()
    tracing_mgr.shutdown()


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error,
            detail=detail,
            status_code=status_code,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(),
    )


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    application = FastAPI(
        title="Graph Analytics API",
        description="REST API for graph-based analytics including UBO discovery, AML detection, and fraud analysis",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        dependencies=[Depends(verify_auth)],
    )

    application.state.limiter = limiter

    settings = get_settings()
    _allow_credentials = settings.api_cors_origins != "*"

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _error_response(429, "rate_limit_exceeded", "Too many requests. Slow down.")

    @application.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "http_error", str(exc.detail))

    @application.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(500, "internal_error", "An unexpected error occurred.")

    application.include_router(health.router)
    application.include_router(ubo.router)
    application.include_router(aml.router)
    application.include_router(fraud.router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "src.python.api.main:app",
        host=_settings.api_host,
        port=_settings.api_port,
        reload=True,
        log_level=_settings.log_level.lower(),
    )
