from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from petland.bootstrap.errors import problem_response, problem_responses, register_handlers
from petland.bootstrap.logging import configure_logging
from petland.bootstrap.settings import Settings
from petland.modules.system.application.readiness import CheckReadiness, ReadinessProbe
from petland.modules.system.infrastructure.readiness import PostgresReadinessProbe
from petland.modules.system.presentation.http.router import create_router
from petland.shared.database import build_engine


def create_app(settings: Settings | None = None, probe: ReadinessProbe | None = None) -> FastAPI:
    configuration = settings or Settings()
    logger = configure_logging(configuration.log_level)
    engine = build_engine(
        configuration.database_url.get_secret_value(),
        configuration.db_connect_timeout,
        configuration.db_statement_timeout_ms,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    local = configuration.app_env in {"development", "test"}
    app = FastAPI(
        title="PetLand API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if local else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if local else None,
        responses=problem_responses(),
    )
    app.include_router(create_router(CheckReadiness(probe or PostgresReadinessProbe(engine))))
    register_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = str(uuid4())
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "unhandled_error",
                extra={"request_id": request.state.request_id, "error_type": type(exc).__name__},
            )
            response = problem_response(request, 500)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        route = request.scope.get("route")
        logger.info(
            "http_request",
            extra={
                "request_id": request.state.request_id,
                "route": getattr(route, "path", "<unmatched>"),
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return response

    return app
