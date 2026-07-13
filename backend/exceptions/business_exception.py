from __future__ import annotations

from typing import Any, Dict, Optional


class BusinessException(Exception):
    """A stable, user-facing API failure."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        field_errors: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field_errors = field_errors

    def detail(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.field_errors:
            result["field_errors"] = self.field_errors
        return result


# Compatibility name used inside services; the public architecture exposes
# BusinessException as the canonical exception type.
ApiError = BusinessException
