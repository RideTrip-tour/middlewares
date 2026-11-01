import asyncio
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.internal_middleware import (
    request_id_var,
    build_request_id_middleware,
)


def test_request_id_header_happy_path(client: TestClient) -> None:
    request_id = "test-request-123"

    response = client.get(
        "/request-id",
        headers={"x-request-id": request_id},
    )

    assert response.status_code == 200
    assert response.json()["request_id"] == request_id
    assert response.json()["context_request_id"] == request_id
    assert response.headers["x-request-id"] == request_id


def test_request_id_generated_when_header_missing(client: TestClient) -> None:
    response = client.get("/request-id")

    assert response.status_code == 200

    request_id = response.json()["request_id"]

    assert str(uuid.UUID(request_id)) == request_id
    assert response.json()["context_request_id"] == request_id
    assert response.headers["x-request-id"] == request_id


def test_request_id_generated_when_header_invalid(client: TestClient) -> None:
    response = client.get(
        "/request-id",
        headers={"x-request-id": "invalid request id"},
    )

    assert response.status_code == 200

    request_id = response.json()["request_id"]

    assert str(uuid.UUID(request_id)) == request_id
    assert response.headers["x-request-id"] == request_id


def test_request_id_context_reset_between_requests(client: TestClient) -> None:
    first_id = "first-request-id"
    second_id = "second-request-id"

    first_response = client.get(
        "/request-id",
        headers={"x-request-id": first_id},
    )
    second_response = client.get(
        "/request-id",
        headers={"x-request-id": second_id},
    )

    assert first_response.json()["context_request_id"] == first_id
    assert second_response.json()["context_request_id"] == second_id


def test_custom_header_name() -> None:
    app = FastAPI()
    app.middleware("http")(
        build_request_id_middleware(
            header_name="X-Correlation-ID",
        )
    )

    @app.get("/request-id")
    async def get_request_id(request: Request):
        return {"request_id": request.state.request_id}

    client = TestClient(app)
    request_id = "custom-request-id"

    response = client.get(
        "/request-id",
        headers={"x-correlation-id": request_id},
    )

    assert response.status_code == 200
    assert response.json()["request_id"] == request_id
    assert response.headers["x-correlation-id"] == request_id


def test_request_id_context_reset_on_exception() -> None:
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-request-id", b"exception-request-id")],
            "method": "GET",
            "path": "/error",
            "query_string": b"",
        }
    )

    middleware = build_request_id_middleware()

    async def call_next(request: Request) -> Response:
        assert request_id_var.get() == "exception-request-id"
        raise RuntimeError("Test exception")

    async def run_test() -> None:
        with pytest.raises(RuntimeError, match="Test exception"):
            await middleware(request, call_next)

        assert request_id_var.get() is None

    asyncio.run(run_test())
