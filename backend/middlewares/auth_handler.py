from __future__ import annotations

from typing import Dict

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.exceptions.business_exception import BusinessException


def is_auth_error(exc: BusinessException) -> bool:
    return exc.status_code in {401, 403}


def auth_error_response(
    request: Request,
    exc: BusinessException,
    headers: Dict[str, str],
) -> JSONResponse:
    """Convert authentication and authorization failures uniformly."""

    detail = exc.detail()
    detail["request_id"] = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=headers,
    )
