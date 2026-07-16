from __future__ import annotations

import argparse
import contextlib
import io
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from tools import knowledge_governance as governance
from backend.constant.values import TYPE_CATEGORIES
from backend.domain.req import (
    SuperAdminKnowledgeAction,
    SuperAdminKnowledgeCommit,
    SuperAdminKnowledgeInput,
)
from backend.exceptions.business_exception import ApiError
from backend.service.member_service import MemberService
from backend.service.preview_nonce_service import PreviewNonceStore
from backend.service.preview_token_service import PreviewTokenService
from backend.service.repository_lock import RepositoryWriteLock
from backend.utils.security import canonical_sha256


class SuperAdminService:
    def __init__(
        self,
        repo: Path,
        members: MemberService,
        write_lock: RepositoryWriteLock,
        preview_tokens: PreviewTokenService,
    ) -> None:
        self.repo = repo.resolve()
        self.members = members
        self.write_lock = write_lock
        self.preview_tokens = preview_tokens
        self.preview_nonces = PreviewNonceStore(repo)

    def _current_admin(self, actor: Dict[str, str]) -> Dict[str, str]:
        current = self.members.get_member(actor["id"])
        self.members.require_role(current, "super_admin")
        return current

    def _locate(self, knowledge_id: str) -> Tuple[Path, Dict[str, Any], str]:
        matches: List[Tuple[Path, Dict[str, Any], str]] = []
        for path in governance.iter_candidate_files(self.repo):
            if not governance.is_entry_file(path):
                continue
            metadata, body = governance.read_entry(path)
            if metadata.get("id") == knowledge_id:
                matches.append((path, metadata, body))
        if not matches:
            raise ApiError(404, "knowledge_not_found", "知识不存在")
        if len(matches) > 1:
            raise ApiError(409, "duplicate_knowledge_id", "知识 ID 在仓库中不唯一")
        path, metadata, body = matches[0]
        try:
            governance.require_valid_entry(self.repo, path, metadata, body)
        except governance.GovernanceError as exc:
            raise ApiError(409, "invalid_knowledge_entry", str(exc)) from exc
        return path, metadata, body

    def _digest(self, path: Path, metadata: Dict[str, Any], body: str) -> str:
        return canonical_sha256(
            {
                "relative_path": path.relative_to(self.repo).as_posix(),
                "metadata": metadata,
                "body": body,
            }
        )

    @staticmethod
    def _content_without_title(metadata: Dict[str, Any], body: str) -> str:
        return governance_text_without_title(metadata, body)

    def _domain_for_path(self, path: Path, metadata: Dict[str, Any]) -> Optional[str]:
        if metadata.get("layer") != "layer2":
            return None
        parts = path.relative_to(self.repo).parts
        return parts[1] if len(parts) > 1 and parts[0] == "biz-wiki" else None

    def _serialize(
        self,
        path: Path,
        metadata: Dict[str, Any],
        body: str,
        *,
        include_content: bool,
    ) -> Dict[str, Any]:
        _layer, _root, archived, _active = governance.layer_context(self.repo, path)
        result: Dict[str, Any] = {
            "id": metadata["id"],
            "title": metadata["title"],
            "type": metadata["type"],
            "scope": governance.metadata_scope(metadata),
            "owner_id": metadata.get("owner_id"),
            "layer": metadata["layer"],
            "domain": self._domain_for_path(path, metadata),
            "technical_direction": governance.entry_technical_direction(
                self.repo,
                path,
                metadata,
            ),
            "maturity": metadata["maturity"],
            "created_at": metadata["created_at"],
            "updated_at": metadata.get("updated_at"),
            "updated_by": metadata.get("updated_by"),
            "revision": governance.entry_revision(metadata),
            "tags": metadata.get("tags", []),
            "source_references": metadata.get("source_references", []),
            "relative_path": path.relative_to(self.repo).as_posix(),
            "archived": archived,
            "conflict_status": metadata.get("conflict_status"),
            "promotion": deepcopy(metadata.get("promotion", {})),
            "evidence": deepcopy(metadata.get("evidence", {})),
            "base_digest": self._digest(path, metadata, body),
        }
        if include_content:
            result["content"] = self._content_without_title(metadata, body)
        return result

    def list_entries(
        self,
        actor: Dict[str, str],
        *,
        state: str = "active",
        layer: Optional[str] = None,
        scope: Optional[str] = None,
        maturity: Optional[str] = None,
        query: str = "",
    ) -> Dict[str, Any]:
        self._current_admin(actor)
        normalized_query = query.strip().casefold()
        items: List[Dict[str, Any]] = []
        counts = {"active": 0, "archived": 0}
        for path in governance.iter_candidate_files(self.repo):
            if not governance.is_entry_file(path):
                continue
            metadata, body = governance.read_entry(path)
            try:
                governance.require_valid_entry(self.repo, path, metadata, body)
            except governance.GovernanceError as exc:
                raise ApiError(409, "invalid_knowledge_entry", str(exc)) from exc
            _entry_layer, _root, archived, _active = governance.layer_context(self.repo, path)
            counts["archived" if archived else "active"] += 1
            if state == "active" and archived:
                continue
            if state == "archived" and not archived:
                continue
            if layer and metadata.get("layer") != layer:
                continue
            if scope and governance.metadata_scope(metadata) != scope:
                continue
            if maturity and metadata.get("maturity") != maturity:
                continue
            item = self._serialize(path, metadata, body, include_content=False)
            searchable = " ".join(
                [
                    str(item["id"]),
                    str(item["title"]),
                    str(item["type"]),
                    str(item.get("owner_id") or ""),
                    " ".join(str(tag) for tag in item["tags"]),
                    self._content_without_title(metadata, body),
                ]
            ).casefold()
            if normalized_query and normalized_query not in searchable:
                continue
            item.pop("evidence", None)
            item.pop("promotion", None)
            items.append(item)
        items.sort(
            key=lambda item: (item.get("updated_at") or item["created_at"], item["id"]),
            reverse=True,
        )
        return {"items": items, "counts": counts, "total": len(items)}

    def get_entry(self, actor: Dict[str, str], knowledge_id: str) -> Dict[str, Any]:
        self._current_admin(actor)
        path, metadata, body = self._locate(knowledge_id)
        return {"knowledge": self._serialize(path, metadata, body, include_content=True)}

    @staticmethod
    def _form_data(request: SuperAdminKnowledgeInput) -> Dict[str, Any]:
        return request.model_dump(mode="json", exclude={"preview_token"})

    @classmethod
    def _form_digest(cls, request: SuperAdminKnowledgeInput) -> str:
        return canonical_sha256(cls._form_data(request))

    def _target_path(
        self,
        request: SuperAdminKnowledgeInput,
        knowledge_id: str,
        source: Path,
    ) -> Path:
        filename = f"{knowledge_id}.md"
        category = TYPE_CATEGORIES[request.type]
        if request.scope == "personal":
            assert request.owner_id is not None
            self.members.get_member(request.owner_id)
            target = (
                self.repo
                / "personal-prefernece"
                / request.owner_id
                / "knowledge"
                / category
                / filename
            )
        else:
            assert request.layer is not None
            if request.layer == "layer0t":
                target = self.repo / "team-conventions" / category / filename
            elif request.layer == "layer1":
                target = self.repo / "tech-wiki" / category / filename
            elif request.layer == "layer2":
                assert request.domain is not None
                domains = {item["id"]: item for item in self.members.list_business_domains()}
                domain = domains.get(request.domain)
                current_domain = source.relative_to(self.repo).parts[1] if source.relative_to(self.repo).parts[0] == "biz-wiki" else None
                if domain is None or (domain["status"] != "active" and request.domain != current_domain):
                    raise ApiError(
                        422,
                        "invalid_domain",
                        "业务领域不存在或已停用",
                        field_errors={"domain": "请选择启用的业务领域"},
                    )
                target = self.repo / "biz-wiki" / request.domain / category / filename
            else:
                target = self.repo / "docs" / "knowledge" / category / filename
        try:
            return governance.resolve_inside(self.repo, str(target))
        except governance.GovernanceError as exc:
            raise ApiError(422, "unsafe_path", str(exc)) from exc

    def _updates(self, request: SuperAdminKnowledgeInput) -> Dict[str, Any]:
        layer = "layer0p" if request.scope == "personal" else request.layer
        return {
            "title": request.title,
            "type": request.type,
            "layer": layer,
            "scope": request.scope,
            "tags": request.tags,
            "source_references": request.source_references,
            "technical_direction": request.technical_direction,
            "owner_id": request.owner_id,
        }

    def _check_owner_confirmation(
        self,
        metadata: Dict[str, Any],
        request: SuperAdminKnowledgeInput,
    ) -> None:
        old_scope = governance.metadata_scope(metadata)
        old_owner = metadata.get("owner_id")
        if old_scope == "personal" and request.scope == "team":
            if request.owner_confirmed_by != old_owner:
                raise ApiError(
                    422,
                    "owner_confirmation_required",
                    f"个人知识转为团队知识前必须由所有者 {old_owner} 确认",
                    field_errors={"owner_confirmed_by": "请填写原所有者 ID"},
                )
        if request.scope == "personal" and (
            old_scope != "personal" or request.owner_id != old_owner
        ):
            if request.owner_confirmed_by != request.owner_id:
                raise ApiError(
                    422,
                    "owner_confirmation_required",
                    f"转为个人知识或更换所有者前必须由新所有者 {request.owner_id} 确认",
                    field_errors={"owner_confirmed_by": "请填写新所有者 ID"},
                )

    def _prepare(
        self,
        path: Path,
        metadata: Dict[str, Any],
        body: str,
        request: SuperAdminKnowledgeInput,
        actor_id: str,
        updated_at: Optional[str] = None,
    ) -> Tuple[Path, Dict[str, Any], str, List[str]]:
        _layer, _root, archived, _active = governance.layer_context(self.repo, path)
        if archived:
            raise ApiError(409, "archived_knowledge", "归档知识必须恢复后才能修改")
        if self._digest(path, metadata, body) != request.base_digest:
            raise ApiError(409, "knowledge_changed", "知识已被其他操作修改，请重新加载")
        self._check_owner_confirmation(metadata, request)
        target = self._target_path(request, str(metadata["id"]), path)
        if target != path and target.exists():
            raise ApiError(409, "knowledge_path_exists", "目标存储路径已存在")
        next_metadata, next_body = governance.prepare_admin_update(
            metadata,
            updates=self._updates(request),
            content=request.content,
            actor=actor_id,
            updated_at=updated_at,
        )
        errors = governance.validate_metadata(next_metadata, next_body)
        errors.extend(governance.validate_path_metadata(self.repo, target, next_metadata))
        if errors:
            raise ApiError(422, "governance_validation_failed", "; ".join(errors))
        changed_fields = sorted(
            field
            for field in governance.ADMIN_EDITABLE_FIELDS
            if metadata.get(field) != next_metadata.get(field)
        )
        if body != next_body:
            changed_fields.append("content")
        if path != target:
            changed_fields.append("relative_path")
        if not changed_fields:
            raise ApiError(422, "no_changes", "没有需要保存的知识修改")
        return target, next_metadata, next_body, sorted(set(changed_fields))

    def preview(
        self,
        actor: Dict[str, str],
        knowledge_id: str,
        request: SuperAdminKnowledgeInput,
    ) -> Dict[str, Any]:
        with self.write_lock.acquire():
            current = self._current_admin(actor)
            path, metadata, body = self._locate(knowledge_id)
            target, next_metadata, next_body, changed_fields = self._prepare(
                path,
                metadata,
                body,
                request,
                current["id"],
            )
            claims = {
                "kind": "super_admin_update",
                "actor": current["id"],
                "knowledge_id": knowledge_id,
                "form_digest": self._form_digest(request),
                "base_digest": request.base_digest,
                "source_path": path.relative_to(self.repo).as_posix(),
                "target_path": target.relative_to(self.repo).as_posix(),
                "after_digest": canonical_sha256(
                    {
                        "metadata": next_metadata,
                        "body": next_body,
                        "relative_path": target.relative_to(self.repo).as_posix(),
                    }
                ),
                "updated_at": next_metadata["updated_at"],
            }
            token, expires_at, signed_claims = self.preview_tokens.issue(claims)
            self.preview_nonces.remember_preview(
                jti=signed_claims["jti"],
                expires_at=signed_claims["exp"],
                actor=current["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=claims["source_path"],
            )
        before = self._serialize(path, metadata, body, include_content=True)
        after = self._serialize(target, next_metadata, next_body, include_content=True)
        consequences = [
            f"revision {governance.entry_revision(metadata)} → {next_metadata['revision']}",
            f"maturity {metadata['maturity']} → draft",
            "旧版本证据保留，但不再推动当前版本成熟度",
        ]
        if path != target:
            consequences.append(
                f"文件移动：{path.relative_to(self.repo).as_posix()} → {target.relative_to(self.repo).as_posix()}"
            )
        return {
            "before": before,
            "after": after,
            "changed_fields": changed_fields,
            "consequences": consequences,
            "checks": [
                {"key": "permission", "label": "超级管理员身份", "status": "passed", "detail": current["id"]},
                {"key": "version", "label": "原版本未变化", "status": "passed", "detail": request.base_digest},
                {"key": "governance", "label": "元数据与路径", "status": "passed", "detail": target.relative_to(self.repo).as_posix()},
                {"key": "audit", "label": "审计日志", "status": "passed", "detail": "提交时与知识修改原子写入"},
            ],
            "preview_token": token,
            "expires_at": expires_at,
        }

    def commit(
        self,
        actor: Dict[str, str],
        knowledge_id: str,
        request: SuperAdminKnowledgeCommit,
        request_id: str,
    ) -> Dict[str, Any]:
        claims = self.preview_tokens.verify(request.preview_token, allow_expired=True)
        if claims.get("kind") != "super_admin_update":
            raise ApiError(400, "invalid_preview_token", "预览凭证用途无效")
        if claims.get("actor") != actor["id"] or claims.get("knowledge_id") != knowledge_id:
            raise ApiError(403, "preview_actor_mismatch", "预览凭证不属于当前成员或知识")
        if claims.get("form_digest") != self._form_digest(request):
            raise ApiError(409, "preview_form_changed", "修改内容已变化，请重新预览")
        updated_at = claims.get("updated_at")
        try:
            governance.parse_time(updated_at)
        except (TypeError, ValueError) as exc:
            raise ApiError(400, "invalid_preview_token", "预览凭证更新时间无效") from exc

        with self.write_lock.acquire():
            current = self._current_admin(actor)
            existing = self.preview_nonces.lookup(
                jti=claims.get("jti"),
                actor=current["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=str(claims.get("source_path")),
            )
            if existing is not None:
                result = existing.get("result")
                if existing.get("status") == "completed" and isinstance(result, dict):
                    return {**result, "idempotent_replay": True}
                if existing.get("status") == "pending":
                    try:
                        recovered_path, recovered_metadata, recovered_body = self._locate(knowledge_id)
                        recovered_digest = self._digest(
                            recovered_path,
                            recovered_metadata,
                            recovered_body,
                        )
                    except ApiError:
                        recovered_digest = ""
                    if (
                        recovered_digest == claims.get("after_digest")
                        and recovered_path.relative_to(self.repo).as_posix()
                        == claims.get("target_path")
                    ):
                        recovered = self._commit_result(
                            recovered_path,
                            recovered_metadata,
                            recovered_body,
                        )
                        self.preview_nonces.complete(str(claims["jti"]), recovered)
                        return {**recovered, "idempotent_replay": True}
                    raise ApiError(409, "preview_submission_in_progress", "该修改正在提交")
            self.preview_tokens.ensure_not_expired(claims)
            path, metadata, body = self._locate(knowledge_id)
            target, _next_metadata, _next_body, _changed = self._prepare(
                path,
                metadata,
                body,
                request,
                current["id"],
                str(updated_at),
            )
            if path.relative_to(self.repo).as_posix() != claims.get("source_path"):
                raise ApiError(409, "preview_context_changed", "知识路径已变化，请重新预览")
            if target.relative_to(self.repo).as_posix() != claims.get("target_path"):
                raise ApiError(409, "preview_context_changed", "目标路径已变化，请重新预览")
            prepared_digest = canonical_sha256(
                {
                    "metadata": _next_metadata,
                    "body": _next_body,
                    "relative_path": target.relative_to(self.repo).as_posix(),
                }
            )
            if prepared_digest != claims.get("after_digest"):
                raise ApiError(409, "preview_metadata_changed", "派生内容已变化，请重新预览")
            self.preview_nonces.reserve(
                jti=claims.get("jti"),
                expires_at=claims.get("exp"),
                actor=current["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=str(claims.get("source_path")),
            )
            try:
                next_metadata, written_path, _action = governance.update_knowledge_entry(
                    repo=self.repo,
                    source_path=path,
                    target_path=target,
                    updates=self._updates(request),
                    content=request.content,
                    actor=current["id"],
                    role=current["role"],
                    reason=request.reason,
                    request_id=request_id,
                    updated_at=str(updated_at),
                )
                written_metadata, written_body = governance.read_entry(written_path)
                result = self._commit_result(written_path, written_metadata, written_body)
                assert next_metadata["id"] == knowledge_id
                self.preview_nonces.complete(str(claims["jti"]), result)
                return result
            except governance.GovernanceError as exc:
                self.preview_nonces.release(str(claims.get("jti")))
                raise ApiError(422, "governance_write_failed", str(exc)) from exc
            except Exception:
                self.preview_nonces.release(str(claims.get("jti")))
                raise

    def _commit_result(
        self,
        written_path: Path,
        written_metadata: Dict[str, Any],
        written_body: str,
    ) -> Dict[str, Any]:
        return {
            "knowledge": self._serialize(
                written_path,
                written_metadata,
                written_body,
                include_content=True,
            ),
            "writes": [
                {"key": "knowledge_file", "label": "知识文件", "status": "completed", "detail": written_path.relative_to(self.repo).as_posix()},
                {"key": "layer_catalog", "label": "Layer B 分类目录", "status": "completed", "detail": "受影响分类目录已更新"},
                {"key": "global_catalog", "label": "Layer A 全景目录", "status": "completed", "detail": "knowledge-catalog.md"},
                {"key": "audit_log", "label": "审计日志", "status": "completed", "detail": "log.md"},
            ],
            "audit_logged": True,
            "idempotent_replay": False,
        }

    def _managed_files(self) -> Iterable[Path]:
        roots = [
            self.repo / "personal-prefernece",
            self.repo / "team-conventions",
            self.repo / "tech-wiki",
            self.repo / "biz-wiki",
            self.repo / "docs" / "knowledge",
            self.repo / "contributions" / "conflicts",
        ]
        for root in roots:
            if root.exists():
                yield from (path for path in root.rglob("*") if path.is_file())
        for path in (self.repo / "knowledge-catalog.md", self.repo / "log.md"):
            if path.exists():
                yield path

    def _action_snapshots(self) -> Dict[Path, str]:
        return {path: path.read_text(encoding="utf-8") for path in set(self._managed_files())}

    def _restore_action_snapshots(self, snapshots: Dict[Path, str]) -> None:
        current = set(self._managed_files())
        for path in current - set(snapshots):
            if path.exists() and path.is_file():
                path.unlink()
        for path, content in snapshots.items():
            governance.atomic_write(path, content)

    def action(
        self,
        actor: Dict[str, str],
        knowledge_id: str,
        request: SuperAdminKnowledgeAction,
        request_id: str,
    ) -> Dict[str, Any]:
        with self.write_lock.acquire():
            current = self._current_admin(actor)
            path, metadata, _body = self._locate(knowledge_id)
            if request.action == "propose_promotion" and request.target_layer == "layer2":
                active_domains = {item["id"] for item in self.members.knowledge_options()["business_domains"]}
                if request.domain not in active_domains:
                    raise ApiError(422, "invalid_domain", "请选择启用的业务领域")
            destination = None
            if request.action == "propose_promotion":
                category = TYPE_CATEGORIES[str(metadata["type"])]
                destination = category if request.target_layer == "layer1" else f"{request.domain}/{category}"
            args = argparse.Namespace(
                repo=str(self.repo),
                path=str(path),
                actor=current["id"],
                role=current["role"],
                session=f"web:super-admin:{request_id}",
                reason=request.reason,
                resolution=request.reason,
                target_layer=request.target_layer,
                destination=destination,
                owner_approved_by=request.owner_confirmed_by,
                owner_confirmed_by=request.owner_confirmed_by,
            )
            handlers = {
                "approve_proven": governance.approve_proven_action,
                "propose_promotion": governance.propose_promotion_action,
                "approve_promotion": governance.approve_promotion_action,
                "rollback_layer": governance.rollback_layer_action,
                "archive": governance.archive_action,
                "restore": governance.restore_action,
                "mark_conflict": governance.mark_conflict_action,
                "resolve_conflict": governance.resolve_conflict_action,
            }
            snapshots = self._action_snapshots()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    handlers[request.action](args)
                detail = json.dumps(
                    {
                        "request_id": request_id,
                        "reason": request.reason,
                        "governance_action": request.action,
                        "result": "success",
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                governance.append_log(
                    self.repo,
                    current["id"],
                    "admin-governance-action",
                    knowledge_id,
                    detail,
                    "web:super-admin",
                )
            except governance.GovernanceError as exc:
                self._restore_action_snapshots(snapshots)
                raise ApiError(422, "governance_action_failed", str(exc)) from exc
            except Exception:
                self._restore_action_snapshots(snapshots)
                raise
            result_path, result_metadata, result_body = self._locate(knowledge_id)
            return {
                "knowledge": self._serialize(
                    result_path,
                    result_metadata,
                    result_body,
                    include_content=True,
                ),
                "action": request.action,
                "audit_logged": True,
            }

    def audit(
        self,
        actor: Dict[str, str],
        *,
        query: str = "",
        action: str = "",
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        self._current_admin(actor)
        path = self.repo / "log.md"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        items: List[Dict[str, Any]] = []
        normalized_query = query.strip().casefold()
        for line in reversed(lines):
            if not line.startswith("- "):
                continue
            parts = line[2:].split(" | ", 5)
            if len(parts) != 6:
                continue
            timestamp, raw_actor, raw_action, raw_target, raw_detail, raw_session = parts
            record_action = raw_action.strip("`")
            if action and record_action != action:
                continue
            searchable = line.casefold()
            if normalized_query and normalized_query not in searchable:
                continue
            detail: Any = raw_detail
            try:
                detail = json.loads(raw_detail)
            except json.JSONDecodeError:
                pass
            items.append(
                {
                    "timestamp": timestamp,
                    "actor": raw_actor.strip("`"),
                    "action": record_action,
                    "target_id": raw_target.strip("`"),
                    "detail": detail,
                    "session": raw_session.strip("`"),
                }
            )
        total = len(items)
        return {"items": items[offset : offset + limit], "total": total}


def governance_text_without_title(metadata: Dict[str, Any], body: str) -> str:
    content = body.lstrip()
    heading = f"# {metadata['title']}"
    if content.startswith(heading):
        content = content[len(heading) :].lstrip("\r\n")
    return content.rstrip()
