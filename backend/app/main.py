from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.websockets.simulation_ws import websocket_router
from app.config import get_settings
from app.core.events import on_shutdown, on_startup
from app.core.middleware import RequestIDMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Nyayrithm API",
        description="Multi-modal agent-driven legal reasoning and courtroom simulation platform",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Exception handler must be registered BEFORE middleware so that
    # unhandled exceptions are converted to a proper Response object
    # *inside* the app boundary.  Without this, ServerErrorMiddleware
    # (outermost Starlette layer) catches the exception AFTER
    # CORSMiddleware has already given up on adding headers, so the
    # browser sees a 500 with no Access-Control-Allow-Origin header.
    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # CORSMiddleware must be added LAST so it becomes the outermost
    # user-added middleware (add_middleware stacks in reverse order).
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(websocket_router)

    return app


app = create_app()
