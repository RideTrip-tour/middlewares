import uuid
from contextvars import ContextVar

user_claims: ContextVar[dict | None] = ContextVar("user_claims", default=None)
request_id_var: ContextVar[str] = ContextVar("request_id", default=str(uuid.uuid4()))
