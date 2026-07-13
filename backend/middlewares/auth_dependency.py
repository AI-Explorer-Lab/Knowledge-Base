from __future__ import annotations

import hashlib
import hmac
import re
import time
from typing import Any, Dict

from fastapi import Request

from backend.constant.values import (
    IDENTITY_ACTOR_HEADER,
    IDENTITY_SIGNATURE_HEADER,
    IDENTITY_TIMESTAMP_HEADER,
)
from backend.exceptions.business_exception import ApiError


ACTOR_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


class IdentityService:
    """Resolve only a server-trusted actor; roles always come from config."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def resolve_actor(self, request: Request) -> str:
        if self.settings.environment_name in {"development", "test"}:
            actor = self.settings.dev_actor
        else:
            actor = self._resolve_signed_proxy_identity(request)
        if not ACTOR_PATTERN.fullmatch(actor):
            raise ApiError(401, "invalid_identity", "已认证的成员 ID 格式无效")
        return actor

    def _resolve_signed_proxy_identity(self, request: Request) -> str:
        actor = request.headers.get(IDENTITY_ACTOR_HEADER, "")
        timestamp_text = request.headers.get(IDENTITY_TIMESTAMP_HEADER, "")
        supplied_signature = request.headers.get(IDENTITY_SIGNATURE_HEADER, "")
        try:
            timestamp = int(timestamp_text)
        except ValueError as exc:
            raise ApiError(401, "missing_identity", "缺少有效的受信身份断言") from exc
        if abs(int(time.time()) - timestamp) > self.settings.identity_max_skew_seconds:
            raise ApiError(401, "stale_identity", "受信身份断言已过期")
        secret = self.settings.identity_hmac_secret
        if secret is None:
            raise ApiError(500, "identity_not_configured", "生产身份验证未配置")
        expected = hmac.new(
            secret,
            f"{timestamp}:{actor}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected):
            raise ApiError(401, "invalid_identity_signature", "受信身份断言签名无效")
        return actor


def current_member(request: Request) -> Dict[str, str]:
    actor = request.app.state.identity.resolve_actor(request)
    return request.app.state.members.get_member(actor)
