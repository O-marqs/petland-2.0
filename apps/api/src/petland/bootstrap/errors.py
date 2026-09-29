from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from petland.shared.domain.errors import BusinessError


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
    401: ("AUTH_REQUIRED", "Entre na sua conta para continuar."),
    403: ("FORBIDDEN", "Sua conta não tem permissão para esta ação."),
    409: ("CONFLICT", "O estado mudou. Atualize a página e tente novamente."),
    413: ("BODY_TOO_LARGE", "A solicitação excede o tamanho permitido."),
    429: ("RATE_LIMITED", "Muitas tentativas. Aguarde 15 minutos antes de tentar novamente."),
    404: ("NOT_FOUND", "O recurso solicitado não foi encontrado."),
    405: ("METHOD_NOT_ALLOWED", "Este método não está disponível para o recurso."),
    422: ("VALIDATION_ERROR", "Revise os campos indicados."),
    500: ("INTERNAL_ERROR", "Não foi possível concluir agora."),
    503: ("SERVICE_UNAVAILABLE", "O serviço está temporariamente indisponível."),
}

IDENTITY_ERRORS = {
    "INVALID_CALENDAR": "Confira os horários, as pausas e os prazos da agenda.",
    "INVALID_WORKER": "Selecione uma pessoa da equipe com conta ativa e e-mail confirmado.",
    "RESOURCE_EXISTS": "Essa pessoa já está cadastrada na capacidade da agenda.",
    "INVALID_BOOKING": "Confira os dados da reserva e informe o motivo da alteração.",
    "CALENDAR_IMPACT": "A alteração afetaria reservas existentes. Revise o impacto e ajuste essas reservas primeiro.",
    "FUTURE_BOOKINGS": "Existem reservas para este cadastro. Reagende ou cancele antes desta alteração.",
    "OFFER_CHANGED": "O serviço ou a agenda mudou. Consulte os horários e revise o resumo novamente.",
    "SLOT_UNAVAILABLE": "Esse horário não está mais disponível. Escolha outra opção.",
    "BOOKING_CLOSED": "Esta reserva não aceita mais alterações.",
    "CHANGE_WINDOW_CLOSED": "O prazo para alterar pela sua conta terminou. Entre em contato com a equipe.",
    "IDEMPOTENCY_MISMATCH": "Essa tentativa já foi usada com outros dados. Inicie uma nova confirmação.",
    "SCHEDULE_BUSY": "A agenda está ocupada no momento. Tente confirmar novamente.",
    "INVALID_TRANSITION": "Esta ação não está disponível neste estado ou horário. Atualize o atendimento.",
    "RESOURCE_IN_PROGRESS": "A pessoa responsável ainda está em outro atendimento. Conclua o cuidado anterior ou ajuste a pessoa responsável antes de iniciar.",
    "INVALID_EXTENSION": "Informe um término posterior ao horário atual e ao reservado, em até oito horas após o término previsto.",
    "EXTENSION_UNAVAILABLE": "O período não cabe no expediente ou conflita com outra reserva. Consulte a agenda e ajuste o horário ou a pessoa responsável.",
    "REASON_REQUIRED": "Informe o motivo para registrar esta alteração.",
    "INVALID_PERIOD": "Escolha um período de até 31 dias, com o início anterior ou igual ao fim.",
    "INVALID_CREDENTIALS": "E-mail ou senha inválidos.",
    "AUTH_REQUIRED": "Entre na sua conta para continuar.",
    "CSRF_REJECTED": "Sua sessão de segurança expirou. Atualize a página e tente novamente.",
    "INVALID_TOKEN": "Este link é inválido, já foi usado ou expirou. Solicite um novo link.",
    "WEAK_PASSWORD": "Use uma senha de 15 a 128 caracteres, evitando senhas comuns ou repetitivas. Espaços são permitidos.",
    "EMAIL_NOT_VERIFIED": "Confirme seu e-mail antes de acessar esta área.",
    "FORBIDDEN": "Sua conta não tem permissão para esta ação.",
    "REAUTHENTICATION_FAILED": "Não foi possível confirmar sua senha atual.",
    "LAST_ADMIN": "É necessário manter pelo menos um administrador ativo.",
    "STALE_VERSION": "Este registro foi alterado. Recarregue os dados antes de tentar novamente.",
    "PROFILE_EXISTS": "Sua conta já tem um cadastro. Procure a equipe para revisar o vínculo.",
    "LINKED_EMAIL": "O e-mail de um cadastro vinculado é o e-mail da conta e não pode ser alterado aqui.",
    "INVALID_REFERENCE": "Confira a espécie, a raça e os portes selecionados.",
    "INVALID_PET": "Confira o nome, o porte e a data de nascimento do pet.",
    "INVALID_SERVICE": "Informe preço e duração válidos para cada porte oferecido.",
    "PET_ARCHIVED": "Restaure o pet antes de editar suas informações.",
    "ROLES_REQUIRED": "Selecione pelo menos um perfil.",
    "BOOTSTRAP_CLOSED": "O primeiro administrador já foi provisionado.",
    "RATE_LIMITED": "Muitas tentativas. Aguarde 15 minutos antes de tentar novamente.",
    "NOT_FOUND": "O recurso solicitado não foi encontrado.",
}


def problem_response(
    request: Request,
    status: int,
    errors: list[dict[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
    identity_code: str | None = None,
) -> JSONResponse:
    code, detail = PUBLIC_ERRORS.get(
        status, ("HTTP_ERROR", "Não foi possível concluir a solicitação.")
    )
    if identity_code in IDENTITY_ERRORS:
        code, detail = identity_code, IDENTITY_ERRORS[identity_code]
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
    @app.exception_handler(BusinessError)
    async def identity_error(request: Request, exc: BusinessError) -> JSONResponse:
        return problem_response(
            request,
            exc.status,
            headers={"Retry-After": "900"} if exc.status == 429 else None,
            identity_code=exc.code,
        )

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
        for status in (400, 401, 403, 404, 405, 409, 413, 422, 429, 500, 503)
    }
