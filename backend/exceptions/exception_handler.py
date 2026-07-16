from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.exceptions.business_exception import BusinessException
from backend.middlewares.auth_handler import auth_error_response, is_auth_error


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _headers(request: Request) -> Dict[str, str]:
    request_id = _request_id(request)
    return {"X-Request-ID": request_id} if request_id else {}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_error(
        request: Request,
        exc: BusinessException,
    ) -> JSONResponse:
        request.state.error_code = exc.code
        if is_auth_error(exc):
            return auth_error_response(request, exc, _headers(request))
        detail = exc.detail()
        detail["request_id"] = _request_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=_headers(request),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request.state.error_code = "validation_error"
        field_errors: Dict[str, str] = {}
        for error in exc.errors():
            location = [str(item) for item in error.get("loc", ()) if item != "body"]
            field = ".".join(location) or "request"
            field_errors.setdefault(field, error.get("msg", "字段无效"))
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "code": "validation_error",
                    "message": "请检查表单字段",
                    "field_errors": field_errors,
                    "request_id": _request_id(request),
                }
            },
            headers=_headers(request),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        request.state.error_code = "internal_error"
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "code": "internal_error",
                    "message": "服务端写入失败，仓库已尽可能恢复，请稍后重试",
                    "request_id": _request_id(request),
                }
            },
            headers=_headers(request),
        )
