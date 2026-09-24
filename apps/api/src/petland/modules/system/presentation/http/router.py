from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from petland.modules.system.application.readiness import CheckReadiness


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok", "ready"]


def create_router(readiness: CheckReadiness) -> APIRouter:
    router = APIRouter(prefix="/api/v1/health", tags=["system"])

    @router.get("/live", response_model=HealthResponse, operation_id="getLiveness")
    def live() -> HealthResponse:
        return HealthResponse(status="ok")

    @router.get("/ready", response_model=HealthResponse, operation_id="getReadiness")
    def ready() -> HealthResponse:
        if not readiness.execute():
            raise HTTPException(status_code=503)
        return HealthResponse(status="ready")

    return router
