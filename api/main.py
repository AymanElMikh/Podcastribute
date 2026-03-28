"""FastAPI application entry point for PodcastAI.

Configures middleware, registers all v1 routers, sets up structlog,
and provides the health check endpoint.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.v1 import auth, billing, content, episodes, publish, stream, voice

log = structlog.get_logger(__name__)


def configure_logging() -> None:
    """Configure structlog for structured JSON logging in production.

    Uses human-readable console output in development and JSON in production.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.ENVIRONMENT == "development"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Creates all database tables on startup (idempotent).
    Closes connections cleanly on shutdown.
    """
    configure_logging()
    log.info("startup", environment=settings.ENVIRONMENT)

    from api.db.models import Base
    from api.db.session import _get_engine
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("db_tables_ready")

    yield
    log.info("shutdown")


app = FastAPI(
    title="PodcastAI",
    description="AI-powered podcast content repurposing engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
# If CORS_ORIGINS is set, use that list. Otherwise allow all origins.
_cors_origins: list[str] = (
    [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if settings.CORS_ORIGINS
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/v1")
app.include_router(episodes.router, prefix="/v1")
app.include_router(content.router, prefix="/v1")
app.include_router(publish.router, prefix="/v1")
app.include_router(voice.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(stream.router, prefix="/v1")


@app.get("/v1/health", tags=["meta"])
async def health_check() -> dict:
    """Return API health status.

    Returns:
        Dict with "status": "ok" when the service is healthy.
    """
    return {"status": "ok"}
