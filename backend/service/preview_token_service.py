from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict

from backend.exceptions.business_exception import ApiError


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, "invalid_preview_token", "预览凭证格式无效") from exc


class PreviewTokenService:
    def __init__(self, secret: bytes, ttl_seconds: int) -> None:
        self._secret = secret
        self.ttl_seconds = ttl_seconds

    def issue(self, claims: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
        issued_at = int(time.time())
        expires_at = issued_at + self.ttl_seconds
        payload = {
            "v": 1,
            **claims,
            "jti": secrets.token_urlsafe(18),
            "iat": issued_at,
            "exp": expires_at,
        }
        encoded = _encode(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
                "utf-8"
            )
        )
        signature = _encode(hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest())
        expires_iso = (
            datetime.fromtimestamp(expires_at, timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        return f"{encoded}.{signature}", expires_iso, payload

    def verify(self, token: str, *, allow_expired: bool = False) -> Dict[str, Any]:
        try:
            encoded, supplied_signature = token.split(".", 1)
        except ValueError as exc:
            raise ApiError(400, "invalid_preview_token", "预览凭证格式无效") from exc
        expected = _encode(hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected):
            raise ApiError(400, "invalid_preview_token", "预览凭证签名无效")
        try:
            payload = json.loads(_decode(encoded))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApiError(400, "invalid_preview_token", "预览凭证内容无效") from exc
        if not isinstance(payload, dict) or payload.get("v") != 1:
            raise ApiError(400, "invalid_preview_token", "预览凭证版本无效")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        now = int(time.time())
        if (
            not isinstance(issued_at, int)
            or not isinstance(expires_at, int)
            or issued_at > now + 5
            or expires_at <= issued_at
        ):
            raise ApiError(400, "invalid_preview_token", "预览凭证时间无效")
        if not allow_expired:
            self.ensure_not_expired(payload)
        return payload

    @staticmethod
    def ensure_not_expired(payload: Dict[str, Any]) -> None:
        expires_at = payload.get("exp")
        if not isinstance(expires_at, int) or expires_at < int(time.time()):
            raise ApiError(409, "preview_expired", "预览已过期，请重新预览后提交")
