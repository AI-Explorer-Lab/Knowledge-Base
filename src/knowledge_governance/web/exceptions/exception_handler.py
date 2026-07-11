import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...errors import KnowledgeError
from .business_exception import BusinessException

LOGGER = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_handler(_: Request, exc: BusinessException):
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "code": exc.code, "message": exc.message})

    @app.exception_handler(KnowledgeError)
    async def knowledge_handler(_: Request, exc: KnowledgeError):
        return JSONResponse(status_code=400, content={"ok": False, "code": "KNOWLEDGE_ERROR", "message": str(exc)})

    @app.exception_handler(Exception)
    async def unknown_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        LOGGER.exception("unhandled request error request_id=%s", request_id)
        return JSONResponse(status_code=500, content={"ok": False, "code": "INTERNAL_ERROR", "message": "服务器处理失败", "request_id": request_id})
