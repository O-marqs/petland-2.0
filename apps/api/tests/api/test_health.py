import io
import json
import logging
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from petland.bootstrap.app import create_app
from petland.bootstrap.logging import JsonFormatter


class Probe:
    def __init__(self, available: bool = True):
        self.available = available
        self.calls = 0

    def is_ready(self) -> bool:
        self.calls += 1
        return self.available


def test_liveness_never_depends_on_database(settings):
    probe = Probe(False)
    with TestClient(create_app(settings, probe)) as client:
        response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert probe.calls == 0


@pytest.mark.parametrize("available,expected", [(True, 200), (False, 503)])
def test_readiness_obeys_probe_and_problem_contract(settings, available, expected):
    with TestClient(create_app(settings, Probe(available))) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == expected
    UUID(response.headers["X-Request-ID"])
    assert response.headers["Cache-Control"] == "no-store"
    if available:
        assert response.json() == {"status": "ready"}
    else:
        assert response.headers["content-type"] == "application/problem+json"
        assert response.json()["code"] == "SERVICE_UNAVAILABLE"
        assert response.json()["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "method,path,status", [("get", "/api/v1/missing", 404), ("post", "/api/v1/health/live", 405)]
)
def test_http_errors_are_consistent(settings, method, path, status):
    with TestClient(create_app(settings, Probe())) as client:
        response = getattr(client, method)(path)
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == status


def test_unexpected_error_and_logs_do_not_leak_secrets(settings):
    class BrokenProbe:
        def is_ready(self) -> bool:
            raise RuntimeError("password=SENSITIVE database connection failed")

    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    app = create_app(settings, BrokenProbe())
    logger = logging.getLogger("petland")
    logger.addHandler(handler)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/health/ready?token=SENSITIVE", headers={"X-Request-ID": "SENSITIVE"}
            )
            client.get("/api/v1/SENSITIVE")
    finally:
        logger.removeHandler(handler)
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "SENSITIVE" not in response.text + output.getvalue()
    logs = [json.loads(line) for line in output.getvalue().splitlines()]
    assert any(log.get("request_id") == response.headers["X-Request-ID"] for log in logs)
    assert logs[-1]["route"] == "<unmatched>"


def test_validation_errors_omit_input_values(settings):
    app = create_app(settings, Probe())

    class RequestBody(BaseModel):
        model_config = ConfigDict(extra="forbid")
        count: int

    @app.post("/_test/validate")
    def validate(body: RequestBody):
        return {"count": body.count}

    with TestClient(app) as client:
        response = client.post("/_test/validate", json={"count": "SECRET_VALUE"})
    assert response.status_code == 422
    assert response.json()["errors"] == [{"field": "body.count", "message": "Valor inválido."}]
    assert "SECRET_VALUE" not in response.text


def test_contract_only_exposes_implemented_endpoints(settings):
    paths = create_app(settings, Probe()).openapi()["paths"]
    assert set(paths) == {"/api/v1/health/live", "/api/v1/health/ready"}
    assert (
        "application/problem+json"
        in paths["/api/v1/health/ready"]["get"]["responses"]["503"]["content"]
    )


def test_real_unreachable_database_fails_closed(settings):
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health/ready").status_code == 503
        assert client.get("/api/v1/health/live").status_code == 200
