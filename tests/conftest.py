import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))



from src.internal_middleware import (
    user_claims,
    request_id_var,
    build_user_context_middleware,
    build_request_id_middleware,
)


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    app.middleware("http")(build_user_context_middleware())
    app.middleware("http")(build_request_id_middleware())

    @app.get("/me")
    async def me():
        return {"claims": user_claims.get()}

    @app.get("/me-state")
    async def me_state(request: Request):
        return {
            "user": getattr(request.state, "user", None),
            "user_id": getattr(request.state, "user_id", None),
        }

    @app.get("/request-id")
    async def get_request_id(request: Request):
        return {
            "request_id": request.state.request_id,
            "context_request_id": request_id_var.get(),
        }

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
