from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str
    request_id: str
    errors: list[dict[str, str]] = Field(default_factory=list)


PUBLIC_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "Não foi possível interpretar a solicitação."),
    404: ("NOT_FOUND", "O recurso solicitado não foi encontrado."),
    405: ("METHOD_NOT_ALLOWED", "Este método não está disponível para o recurso."),
    422: ("VALIDATION_ERROR", "Revise os campos indicados."),
    500: ("INTERNAL_ERROR", "Não foi possível concluir agora."),
    503: ("SERVICE_UNAVAILABLE", "O serviço está temporariamente indisponível."),
}


def problem_response(
    request: Request,
    status: int,
    errors: list[dict[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    code, detail = PUBLIC_ERRORS.get(
        status, ("HTTP_ERROR", "Não foi possível concluir a solicitação.")
    )
    body = Problem(
        title=HTTPStatus(status).phrase,
        status=status,
        code=code,
        detail=detail,
        request_id=request.state.request_id,
        errors=errors or [],
    )
    return JSONResponse(
        body.model_dump(),
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
    )


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return problem_response(request, exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {
                "field": ".".join(str(p) for p in err["loc"] if isinstance(p, (int, str))),
                "message": "Valor inválido.",
            }
            for err in exc.errors()
        ]
        return problem_response(request, 422, fields)


def problem_responses() -> dict[int | str, dict[str, Any]]:
    return {
        status: {
            "content": {"application/problem+json": {"schema": Problem.model_json_schema()}},
            "description": HTTPStatus(status).phrase,
        }
        for status in (404, 405, 422, 500, 503)
    }
