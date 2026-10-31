import logging
import uuid

from fastapi import Request
from starlette.responses import Response

from .context import request_id_var
from .constants import REQUEST_ID_PATTERN


def _get_request_id(
    request: Request,
    header_key: str,
    logger: logging.Logger,
) -> str:
    """Get request_id from header or generate a new one."""

    request_id = request.headers.get(header_key)

    if request_id is None or not REQUEST_ID_PATTERN.fullmatch(request_id):
        request_id = str(uuid.uuid4())
        logger.debug("Generated new request_id: %s", request_id)

    return request_id


def build_request_id_middleware(
    *,
    logger: logging.Logger | None = None,
    header_name: str = "X-Request-ID",
):
    """Фабрика middleware для обработки request_id."""

    log = logger or logging.getLogger(__name__)
    header_key = header_name.lower()

    async def request_id_middleware(
        request: Request,
        call_next,
    ) -> Response:
        request_id = _get_request_id(request, header_key, log)

        request.state.request_id = request_id
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers[header_name] = request_id
            return response
        finally:
            request_id_var.reset(token)

    return request_id_middleware