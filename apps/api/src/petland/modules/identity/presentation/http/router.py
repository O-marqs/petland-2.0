from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from petland.modules.identity.application.service import IdentityService
from petland.modules.identity.domain.models import User
from petland.modules.identity.presentation.http.schemas import (
    AccountResponse,
    ChangePasswordInput,
    CsrfResponse,
    EmailInput,
    InvitationInput,
    InviteEmployeeInput,
    LoginInput,
    Message,
    RegisterInput,
    ResetInput,
    RolesInput,
    SessionResponse,
    StatusInput,
    TokenInput,
    UsersResponse,
)
from petland.modules.identity.public.http import HttpIdentity


def create_identity_router(service: IdentityService, origin: str, secure: bool) -> APIRouter:
    auth = HttpIdentity(service, origin, secure)
    cookie_name = auth.cookie_name
    raw_session, csrf_guard, actor = auth.raw_session, auth.csrf_guard, auth.actor

    def set_cookie(response: Response, raw: str) -> None:
        response.set_cookie(
            cookie_name,
            raw,
            max_age=8 * 3600,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )

    def ip(request: Request) -> str:
        # Never trust client-supplied X-Forwarded-For. Proxy trust is a deployment decision.
        return request.client.host if request.client else "unknown"

    def sensitive_limit(request: Request, user: User) -> None:
        service.limit("sensitive", ip(request), str(user.id), 10)

    router = APIRouter(prefix="/api/v1", tags=["identity"], dependencies=[Depends(csrf_guard)])
    Actor = Annotated[User, Depends(actor)]

    @router.get("/auth/csrf", response_model=CsrfResponse)
    def csrf(request: Request, response: Response) -> CsrfResponse:
        service.limit("csrf", ip(request), maximum=120)
        raw, csrf_token = service.csrf(raw_session(request))
        set_cookie(response, raw)
        return CsrfResponse(csrf_token=csrf_token)

    @router.post("/auth/register", status_code=202, response_model=Message)
    def register(body: RegisterInput, request: Request) -> Message:
        service.limit("register", ip(request), body.email, 5)
        service.register(
            body.email,
            body.display_name,
            body.password.get_secret_value(),
            request.state.request_id,
        )
        return Message(
            message="Se o endereço puder ser cadastrado, você receberá um e-mail para continuar. Se já tem conta, entre ou recupere o acesso."
        )

    @router.post("/auth/login", response_model=AccountResponse)
    def login(body: LoginInput, request: Request, response: Response) -> AccountResponse:
        service.limit("login", ip(request), body.email)
        user, raw = service.login(
            body.email,
            body.password.get_secret_value(),
            raw_session(request),
            request.state.request_id,
        )
        set_cookie(response, raw)
        return AccountResponse.from_user(user)

    @router.post("/auth/logout", status_code=204)
    def logout(request: Request, response: Response) -> None:
        service.logout(raw_session(request), request.state.request_id)
        response.delete_cookie(cookie_name, secure=secure, httponly=True, samesite="lax", path="/")

    @router.get("/auth/me", response_model=AccountResponse)
    def me(user: Actor) -> AccountResponse:
        return AccountResponse.from_user(user)

    @router.post("/auth/password-reset-requests", status_code=202, response_model=Message)
    def request_reset(body: EmailInput, request: Request) -> Message:
        service.limit("reset-request", ip(request), body.email, 5)
        service.request_token(body.email, "reset", request.state.request_id)
        return Message(
            message="Se houver uma conta disponível para este endereço, enviaremos as instruções de recuperação."
        )

    @router.post("/auth/email-verification-requests", status_code=202, response_model=Message)
    def request_verification(body: EmailInput, request: Request) -> Message:
        service.limit("verify-request", ip(request), body.email, 5)
        service.request_token(body.email, "verify", request.state.request_id)
        return Message(
            message="Se a conta precisar de confirmação, enviaremos um novo link para este endereço."
        )

    @router.post("/auth/email-verifications", response_model=Message)
    def verify_email(body: TokenInput, request: Request) -> Message:
        service.limit("consume", ip(request), maximum=20)
        service.consume_token(
            body.token.get_secret_value(), "verify", None, request.state.request_id
        )
        return Message(message="E-mail confirmado. Você já pode entrar na sua conta.")

    @router.post("/auth/password-resets", response_model=Message)
    def reset_password(body: ResetInput, request: Request) -> Message:
        service.limit("consume", ip(request), maximum=20)
        service.consume_token(
            body.token.get_secret_value(),
            "reset",
            body.password.get_secret_value(),
            request.state.request_id,
        )
        return Message(message="Senha redefinida e sessões encerradas. Entre com a nova senha.")

    @router.get("/auth/sessions", response_model=list[SessionResponse])
    def sessions(request: Request, user: Actor) -> list[SessionResponse]:
        current = service.authenticate(raw_session(request))[1]
        return [
            SessionResponse(
                id=item.id,
                created_at=item.created_at,
                last_seen_at=item.last_seen_at,
                expires_at=item.expires_at,
                current=item.id == current.id,
            )
            for item in service.list_sessions(user.id)
        ]

    @router.delete("/auth/sessions/{session_id}", status_code=204)
    def revoke_session(session_id: UUID, request: Request, user: Actor) -> None:
        service.revoke_session(user.id, session_id, request.state.request_id)

    @router.post("/me/password-changes", response_model=Message)
    def change_password(body: ChangePasswordInput, request: Request, user: Actor) -> Message:
        sensitive_limit(request, user)
        service.change_password(
            user.id,
            body.current_password.get_secret_value(),
            body.password.get_secret_value(),
            request.state.request_id,
        )
        return Message(message="Senha alterada. Entre novamente em todos os dispositivos.")

    @router.post("/management/employee-invitations", status_code=202, response_model=Message)
    def invite(body: InviteEmployeeInput, request: Request, user: Actor) -> Message:
        sensitive_limit(request, user)
        service.invite(
            user.id, body.email, body.current_password.get_secret_value(), request.state.request_id
        )
        return Message(
            message="Convite solicitado. O destinatário deve confirmar o e-mail para participar da equipe."
        )

    @router.post("/auth/invitations/accept", response_model=Message)
    def accept_invitation(body: InvitationInput, request: Request) -> Message:
        service.limit("consume", ip(request), maximum=20)
        service.accept_invitation(
            body.token.get_secret_value(),
            body.display_name.strip(),
            body.password.get_secret_value(),
            request.state.request_id,
        )
        return Message(message="Convite aceito. Entre para acessar sua área.")

    @router.get("/management/users", response_model=UsersResponse)
    def users(
        user: Actor,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ) -> UsersResponse:
        items = service.list_users(user.id, offset, limit + 1)
        return UsersResponse(
            items=[AccountResponse.from_user(item) for item in items[:limit]],
            offset=offset,
            limit=limit,
            has_more=len(items) > limit,
        )

    @router.put("/management/users/{user_id}/roles", status_code=204)
    def roles(user_id: UUID, body: RolesInput, request: Request, user: Actor) -> None:
        sensitive_limit(request, user)
        service.manage_user(
            user.id,
            user_id,
            body.current_password.get_secret_value(),
            body.expected_version,
            frozenset(body.roles),
            None,
            request.state.request_id,
        )

    @router.patch("/management/users/{user_id}/status", status_code=204)
    def status(user_id: UUID, body: StatusInput, request: Request, user: Actor) -> None:
        sensitive_limit(request, user)
        service.manage_user(
            user.id,
            user_id,
            body.current_password.get_secret_value(),
            body.expected_version,
            None,
            body.status,
            request.state.request_id,
        )

    return router
