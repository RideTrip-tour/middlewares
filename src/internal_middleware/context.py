from contextvars import ContextVar

user_claims: ContextVar[dict | None] = ContextVar("user_claims", default=None)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)