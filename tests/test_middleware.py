import base64
import json
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.internal_middleware import user_claims, build_user_context_middleware


def _b64url(data: dict) -> str:
    raw = json.dumps(data).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(build_user_context_middleware())

    @app.get("/me")
    async def me():
        return {"claims": user_claims.get()}

    @app.get("/me-state")
    async def me_state(request):
        return {
            "user": getattr(request.state, "user", None),
            "user_id": getattr(request.state, "user_id", None),
        }

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_claims_header_happy_path(client: TestClient) -> None:
    claims = {"user_id": 42, "role": "admin"}
    resp = client.get("/me", headers={"x-user-claims": _b64url(claims)})
    assert resp.status_code == 200
    assert resp.json()["claims"] == claims


def test_user_id_header_int(client: TestClient) -> None:
    resp = client.get("/me-state", headers={"x-user-id": "123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == 123
    assert body["user"] == {"sub": "123", "user_id": 123}


def test_user_id_header_string(client: TestClient) -> None:
    resp = client.get("/me-state", headers={"x-user-id": "abc"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "abc"


def test_no_headers(client: TestClient) -> None:
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["claims"] == {}


def test_invalid_base64(client: TestClient) -> None:
    resp = client.get("/me", headers={"x-user-claims": "!!!not-base64!!!"})
    assert resp.status_code == 401


def test_invalid_json(client: TestClient) -> None:
    bad = base64.urlsafe_b64encode(b"not a json").rstrip(b"=").decode()
    resp = client.get("/me", headers={"x-user-claims": bad})
    assert resp.status_code == 401


def test_json_not_object(client: TestClient) -> None:
    bad = base64.urlsafe_b64encode(b"[1,2,3]").rstrip(b"=").decode()
    resp = client.get("/me", headers={"x-user-claims": bad})
    assert resp.status_code == 401


def test_claims_takes_priority_over_user_id(client: TestClient) -> None:
    claims = {"user_id": 42}
    resp = client.get(
        "/me-state",
        headers={
            "x-user-claims": _b64url(claims),
            "x-user-id": "999",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user_id"] == 42


def test_context_reset_between_requests(client: TestClient) -> None:
    """ContextVar не должен протекать между запросами."""
    client.get("/me", headers={"x-user-claims": _b64url({"user_id": 1})})
    resp = client.get("/me")
    assert resp.json()["claims"] == {}


def test_custom_header_names() -> None:
    app = FastAPI()
    app.middleware("http")(
        build_user_context_middleware(
            claims_header="x-custom-claims",
            user_id_header="x-custom-id",
        )
    )

    @app.get("/me")
    async def me():
        return user_claims.get()

    client = TestClient(app)
    claims = {"user_id": 7}
    resp = client.get("/me", headers={"x-custom-claims": _b64url(claims)})
    assert resp.status_code == 200
    assert resp.json() == claims
