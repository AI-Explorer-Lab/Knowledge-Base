import logging
import time
import uuid

from fastapi import FastAPI, Request

LOGGER = logging.getLogger(__name__)


def register_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        LOGGER.info("request_id=%s method=%s path=%s status=%s elapsed_ms=%.2f", request_id, request.method, request.url.path, response.status_code, elapsed_ms)
        return response
