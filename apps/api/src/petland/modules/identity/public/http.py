from urllib.parse import urlsplit

from fastapi import Request

from petland.modules.identity.application.service import IdentityService
from petland.modules.identity.domain.models import IdentityError, User


class HttpIdentity:
    def __init__(self, service: IdentityService, origin: str, secure: bool) -> None:
        self.service, self.origin, self.secure = service, origin, secure
        self.cookie_name = "__Host-petland_session" if secure else "petland_dev_session"

    def raw_session(self, request: Request) -> str | None:
        raw = request.cookies.get(self.cookie_name)
        return raw if raw and len(raw) <= 128 else None

    def actor(self, request: Request) -> User:
        return self.service.authenticate(self.raw_session(request))[0]

    def csrf_guard(self, request: Request) -> None:
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return
        received = request.headers.get("origin")
        if not received and request.headers.get("referer"):
            parsed = urlsplit(request.headers["referer"])
            received = f"{parsed.scheme}://{parsed.netloc}"
        allowed = {self.origin}
        if not self.secure and self.origin == "http://localhost:5173":
            allowed.add("http://127.0.0.1:5173")
        if received not in allowed or request.headers.get("sec-fetch-site") == "cross-site":
            raise IdentityError("CSRF_REJECTED", 403)
        self.service.verify_csrf(self.raw_session(request), request.headers.get("x-csrf-token", ""))

    def sensitive_limit(self, request: Request, actor: User) -> None:
        ip = request.client.host if request.client else "unknown"
        self.service.limit("sensitive", ip, str(actor.id), 10)
