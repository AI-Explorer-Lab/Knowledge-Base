from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from tools import knowledge_governance as governance
from backend.exceptions.business_exception import ApiError


IDEMPOTENCY_RETENTION_SECONDS = 24 * 60 * 60


class PreviewNonceStore:
    """Repository-local replay and idempotency state shared by all workers.

    Every method must be called while the repository write lock is held.
    A JTI is reserved once; a completed response can then be returned for an
    exact retry without executing repository writes again.
    """

    def __init__(self, repo: Path) -> None:
        self.path = repo.resolve() / ".knowledge-preview-nonces.json"

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ApiError(500, "invalid_preview_state", "预览凭证状态文件无效") from exc
        if not isinstance(raw, dict) or any(
            not isinstance(key, str) or not isinstance(value, dict)
            for key, value in raw.items()
        ):
            raise ApiError(500, "invalid_preview_state", "预览凭证状态文件无效")
        return raw

    def _write(self, state: Dict[str, Dict[str, Any]]) -> None:
        governance.atomic_write(
            self.path,
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

    def reserved_knowledge_ids(self) -> set[str]:
        """IDs held by still-valid previews or in-flight submissions."""

        now = int(time.time())
        return {
            str(record["knowledge_id"])
            for record in self._load().values()
            if record.get("status") in {"previewed", "pending"}
            and isinstance(record.get("exp"), int)
            and record["exp"] >= now
            and isinstance(record.get("knowledge_id"), str)
        }

    def remember_preview(
        self,
        *,
        jti: Any,
        expires_at: Any,
        actor: str,
        form_digest: str,
        knowledge_id: str,
        relative_path: str,
    ) -> None:
        if not isinstance(jti, str) or not jti or not isinstance(expires_at, int):
            raise ApiError(400, "invalid_preview_token", "预览凭证缺少一次性标识")
        state = self._load()
        state[jti] = {
            "actor": actor,
            "form_digest": form_digest,
            "knowledge_id": knowledge_id,
            "relative_path": relative_path,
            "exp": expires_at,
            "retain_until": expires_at + IDEMPOTENCY_RETENTION_SECONDS,
            "status": "previewed",
        }
        self._write(state)

    def reserve(
        self,
        *,
        jti: Any,
        expires_at: Any,
        actor: str,
        form_digest: str,
        knowledge_id: str,
        relative_path: str,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(jti, str) or not jti or not isinstance(expires_at, int):
            raise ApiError(400, "invalid_preview_token", "预览凭证缺少一次性标识")
        now = int(time.time())
        state: Dict[str, Dict[str, Any]] = {}
        for key, value in self._load().items():
            retain_until = value.get("retain_until", value.get("exp"))
            if isinstance(retain_until, int) and retain_until >= now:
                state[key] = value
        identity = {
            "actor": actor,
            "form_digest": form_digest,
            "knowledge_id": knowledge_id,
            "relative_path": relative_path,
        }
        existing = state.get(jti)
        if existing is not None:
            if any(existing.get(key) != value for key, value in identity.items()):
                raise ApiError(409, "preview_replay_conflict", "预览凭证重放与原请求不一致")
            if existing.get("status") == "previewed":
                existing["status"] = "pending"
                state[jti] = existing
                self._write(state)
                return None
            return deepcopy(existing)
        state[jti] = {
            **identity,
            "exp": expires_at,
            "retain_until": expires_at + IDEMPOTENCY_RETENTION_SECONDS,
            "status": "pending",
        }
        self._write(state)
        return None

    def lookup(
        self,
        *,
        jti: Any,
        actor: str,
        form_digest: str,
        knowledge_id: str,
        relative_path: str,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(jti, str) or not jti:
            raise ApiError(400, "invalid_preview_token", "预览凭证缺少一次性标识")
        state = self._load()
        existing = state.get(jti)
        if existing is None:
            return None
        retain_until = existing.get("retain_until", existing.get("exp"))
        if not isinstance(retain_until, int) or retain_until < int(time.time()):
            del state[jti]
            self._write(state)
            return None
        identity = {
            "actor": actor,
            "form_digest": form_digest,
            "knowledge_id": knowledge_id,
            "relative_path": relative_path,
        }
        if any(existing.get(key) != value for key, value in identity.items()):
            raise ApiError(409, "preview_replay_conflict", "预览凭证重放与原请求不一致")
        return deepcopy(existing)

    def complete(self, jti: str, result: Dict[str, Any]) -> None:
        state = self._load()
        record = state.get(jti)
        if not isinstance(record, dict):
            raise ApiError(500, "preview_state_missing", "预览凭证状态丢失")
        record["status"] = "completed"
        record["completed_at"] = int(time.time())
        record["retain_until"] = max(
            int(record.get("retain_until", 0)),
            record["completed_at"] + IDEMPOTENCY_RETENTION_SECONDS,
        )
        record["result"] = result
        self._write(state)

    def release(self, jti: str) -> None:
        """Release a reservation when repository writes were rolled back."""

        state = self._load()
        record = state.get(jti)
        if isinstance(record, dict) and record.get("status") == "pending":
            record["status"] = "previewed"
            self._write(state)
