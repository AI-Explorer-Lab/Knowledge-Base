from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools import knowledge_governance as governance
from backend.constant.enums import KnowledgeLayer
from backend.constant.values import (
    LAYER_PREFIXES,
    TYPE_CATEGORIES,
    TYPE_CODES,
)
from backend.domain.models import KnowledgeTarget
from backend.domain.req import KnowledgeInput, ManualKnowledgeRequest
from backend.exceptions.business_exception import ApiError
from backend.service.member_service import MemberService
from backend.service.preview_nonce_service import PreviewNonceStore
from backend.service.preview_token_service import PreviewTokenService
from backend.service.repository_lock import RepositoryWriteLock
from backend.utils.path_utils import writable_target
from backend.utils.security import canonical_sha256

READABLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")


class KnowledgeService:
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

    @staticmethod
    def _form_data(request: KnowledgeInput) -> Dict[str, Any]:
        return request.model_dump(mode="json", exclude={"preview_token"})

    @classmethod
    def _form_digest(cls, request: KnowledgeInput) -> str:
        return canonical_sha256(cls._form_data(request))

    @staticmethod
    def _metadata_digest(metadata: Dict[str, Any], relative_path: str) -> str:
        return canonical_sha256({"metadata": metadata, "relative_path": relative_path})

    def _member_segment(self, actor: str) -> str:
        observed: List[str] = []
        for path in governance.iter_candidate_files(self.repo):
            if not governance.is_entry_file(path):
                continue
            metadata, _body = governance.read_entry(path)
            if metadata.get("owner_id") != actor:
                continue
            match = re.fullmatch(r"PK-([A-Z0-9]+)-[A-Z]+-\d+", str(metadata.get("id", "")))
            if match:
                observed.append(match.group(1))
        if observed:
            return sorted(observed)[0]
        value = re.sub(r"[^a-z0-9]", "", actor.lower())[:2]
        return value.upper() or "MB"

    def _new_id(self, request: KnowledgeInput, actor: str) -> str:
        if request.scope == "personal":
            code = TYPE_CODES[request.type]
            base = f"PK-{self._member_segment(actor)}-{code}"
        else:
            assert request.layer is not None
            code = TYPE_CODES[request.type]
            base = f"{LAYER_PREFIXES[request.layer]}-{code}"
        occupied = self.preview_nonces.reserved_knowledge_ids()
        for path in governance.iter_candidate_files(self.repo):
            if governance.is_entry_file(path):
                occupied.add(str(governance.read_entry(path)[0].get("id", "")))
        pattern = re.compile(rf"^{re.escape(base)}-(\d+)$")
        numbers = [int(match.group(1)) for item in occupied if (match := pattern.fullmatch(item))]
        return f"{base}-{max(numbers, default=0) + 1:03d}"

    def _derive(
        self,
        request: KnowledgeInput,
        actor: str,
        knowledge_id: str,
    ) -> KnowledgeTarget:
        options = self.members.knowledge_options()
        if request.scope == "personal":
            layer = "layer0p"
            owner_id: Optional[str] = actor
        else:
            assert request.layer is not None
            layer = request.layer
            owner_id = None
        filename = f"{knowledge_id}.md"
        if layer == "layer0p":
            category = TYPE_CATEGORIES[request.type]
            path = self.repo / "personal-prefernece" / actor / "knowledge" / category / filename
        elif layer == "layer1":
            category = TYPE_CATEGORIES[request.type]
            path = self.repo / "tech-wiki" / category / filename
        elif layer == "layer2":
            category = TYPE_CATEGORIES[request.type]
            assert request.domain is not None
            domain_ids = {item["id"] for item in options["business_domains"]}
            if request.domain not in domain_ids:
                raise ApiError(
                    422,
                    "invalid_domain",
                    "业务领域不在后端受控选项中",
                    field_errors={"domain": "请从有效业务领域中选择"},
                )
            path = self.repo / "biz-wiki" / request.domain / category / filename
        else:
            category = TYPE_CATEGORIES[request.type]
            path = self.repo / "docs" / "knowledge" / category / filename
        resolved = governance.resolve_inside(self.repo, str(path))
        actual_layer, _, archived, _ = governance.layer_context(self.repo, resolved)
        if archived or actual_layer != layer or "archive" in resolved.relative_to(self.repo).parts:
            raise ApiError(422, "unsafe_path", "后端派生的存储路径无效")
        return KnowledgeTarget(
            relative_path=resolved.relative_to(self.repo).as_posix(),
            layer=layer,
            owner_id=owner_id,
        )

    def _id_is_unique(self, knowledge_id: str) -> bool:
        for path in governance.iter_candidate_files(self.repo):
            if governance.is_entry_file(path):
                metadata, _body = governance.read_entry(path)
                if metadata.get("id") == knowledge_id:
                    return False
        return True

    def _preflight_checks(
        self,
        *,
        actor: Dict[str, str],
        metadata: Dict[str, Any],
        body: str,
        relative_path: str,
    ) -> List[Dict[str, str]]:
        target = self.repo / relative_path
        errors = governance.validate_metadata(metadata, body)
        errors.extend(governance.validate_path_metadata(self.repo, target, metadata))
        if errors:
            raise ApiError(422, "governance_validation_failed", "; ".join(errors))
        if not self._id_is_unique(metadata["id"]):
            raise ApiError(409, "knowledge_id_conflict", "服务端生成的知识 ID 已存在")
        if target.exists() or not writable_target(target):
            raise ApiError(409, "knowledge_path_conflict", "派生路径已存在或不可写")
        _layer, layer_root, _archived, _relative = governance.layer_context(self.repo, target)
        layer_catalog = layer_root / "catalog.md"
        global_catalog = self.repo / "knowledge-catalog.md"
        if not global_catalog.is_file() or not writable_target(global_catalog):
            raise ApiError(500, "catalog_not_writable", "全局知识目录不可写")
        try:
            catalog_paths = set(governance.expected_catalogs(self.repo))
        except governance.GovernanceError as exc:
            raise ApiError(409, "catalog_preflight_failed", str(exc)) from exc
        catalog_paths.add(layer_catalog)
        unwritable_catalogs = [
            path.relative_to(self.repo).as_posix()
            for path in catalog_paths
            if not writable_target(path)
        ]
        if unwritable_catalogs:
            raise ApiError(
                500,
                "catalog_not_writable",
                "以下分类目录不可写：" + "、".join(unwritable_catalogs),
            )
        log_path = self.repo / "log.md"
        if not (
            (log_path.is_file() and writable_target(log_path))
            or (not log_path.exists() and writable_target(log_path))
        ):
            raise ApiError(500, "audit_log_not_writable", "审计日志不可写")
        return [
            {
                "key": "permission",
                "label": "身份与权限",
                "status": "passed",
                "detail": f"{actor['display_name']} · {actor['role']}",
            },
            {
                "key": "metadata",
                "label": "元数据与正文",
                "status": "passed",
                "detail": "必填字段、默认值和治理结构有效",
            },
            {
                "key": "scope_owner",
                "label": "个人知识所有者一致" if metadata["scope"] == "personal" else "团队范围与层级一致",
                "status": "passed",
                "detail": (
                    f"owner_id = {metadata['owner_id']}"
                    if metadata["scope"] == "personal"
                    else f"scope = team · layer = {metadata['layer']}"
                ),
            },
            {
                "key": "id_path_available",
                "label": "知识 ID 与存储路径",
                "status": "passed",
                "detail": f"{metadata['id']} · {relative_path}",
            },
            {
                "key": "catalog_writable",
                "label": "Layer A / B 索引",
                "status": "passed",
                "detail": f"全局目录与 {len(catalog_paths)} 个分类目录已就绪",
            },
            {
                "key": "audit_log_writable",
                "label": "审计日志",
                "status": "passed",
                "detail": "log.md 已就绪",
            },
        ]

    def options(self) -> Dict[str, Any]:
        configured = self.members.knowledge_options()
        return {
            "scopes": [
                {"value": "personal", "label": "个人知识"},
                {"value": "team", "label": "团队知识"},
            ],
            "knowledge_types": [
                {"value": "model", "label": "模型"},
                {"value": "decision", "label": "决策"},
                {"value": "guideline", "label": "指南"},
                {"value": "pitfall", "label": "陷阱"},
                {"value": "process", "label": "流程"},
            ],
            "layers": [
                {"value": "layer1", "label": "Layer 1 技术知识"},
                {"value": "layer2", "label": "Layer 2 业务知识"},
                {"value": "layer3", "label": "Layer 3 项目知识"},
            ],
            "technical_directions": [
                {"value": "patterns", "label": "正向模式"},
                {"value": "anti-patterns", "label": "反模式"},
            ],
            "business_domains": configured["business_domains"],
            "preview_ttl_seconds": self.preview_tokens.ttl_seconds,
        }

    def preview(self, request: KnowledgeInput, actor: Dict[str, str]) -> Dict[str, Any]:
        with self.write_lock.acquire():
            current_actor = self.members.get_member(actor["id"])
            self.members.require_role(current_actor, "contributor", "maintainer")
            knowledge_id = self._new_id(request, current_actor["id"])
            target = self._derive(
                request,
                current_actor["id"],
                knowledge_id,
            )
            relative_path = target.relative_path
            layer = target.layer
            owner_id = target.owner_id
            created_at = governance.utc_now()
            metadata = governance.build_knowledge_metadata(
                knowledge_id=knowledge_id,
                title=request.title,
                knowledge_type=request.type,
                layer=layer,
                scope=request.scope,
                actor=current_actor["id"],
                sources=request.source_references,
                tags=request.tags,
                technical_direction=request.technical_direction,
                owner_id=owner_id,
                created_at=created_at,
            )
            body = f"# {request.title}\n\n{request.content}\n"
            checks = self._preflight_checks(
                actor=current_actor,
                metadata=metadata,
                body=body,
                relative_path=relative_path,
            )
            claims = {
                "actor": current_actor["id"],
                "form_digest": self._form_digest(request),
                "knowledge_id": knowledge_id,
                "relative_path": relative_path,
                "layer": layer,
                "owner_id": owner_id,
                "created_at": created_at,
                "metadata_digest": self._metadata_digest(metadata, relative_path),
            }
            token, expires_at, signed_claims = self.preview_tokens.issue(claims)
            self.preview_nonces.remember_preview(
                jti=signed_claims["jti"],
                expires_at=signed_claims["exp"],
                actor=current_actor["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=relative_path,
            )
        return {
            "preview": {
                **metadata,
                "technical_direction": request.technical_direction,
                "owner_id": owner_id,
                "relative_path": relative_path,
                "metadata": metadata,
                "content": request.content,
            },
            "preview_token": token,
            "expires_at": expires_at,
            "checks": checks,
        }

    def create(self, request: ManualKnowledgeRequest, actor: Dict[str, str]) -> Dict[str, Any]:
        # Signature and claim structure remain mandatory after expiration so an
        # exact retry can recover an already-completed write without creating a
        # second knowledge ID. Expiration is enforced below before any new write.
        claims = self.preview_tokens.verify(request.preview_token, allow_expired=True)
        if claims.get("actor") != actor["id"]:
            raise ApiError(403, "preview_actor_mismatch", "预览凭证不属于当前成员")
        if claims.get("form_digest") != self._form_digest(request):
            raise ApiError(409, "preview_form_changed", "表单已修改，请重新预览")
        knowledge_id = claims.get("knowledge_id")
        if not isinstance(knowledge_id, str) or not READABLE_ID_PATTERN.fullmatch(knowledge_id):
            raise ApiError(400, "invalid_preview_token", "预览凭证中的知识 ID 无效")

        with self.write_lock.acquire():
            current_actor = self.members.get_member(actor["id"])
            self.members.require_role(current_actor, "contributor", "maintainer")
            target = self._derive(request, current_actor["id"], knowledge_id)
            relative_path = target.relative_path
            layer = target.layer
            owner_id = target.owner_id
            expected = {
                "relative_path": relative_path,
                "layer": layer,
                "owner_id": owner_id,
            }
            if any(claims.get(key) != value for key, value in expected.items()):
                raise ApiError(409, "preview_context_changed", "存储选项已变更，请重新预览")
            created_at = claims.get("created_at")
            try:
                governance.parse_time(created_at)
            except (TypeError, ValueError) as exc:
                raise ApiError(400, "invalid_preview_token", "预览凭证时间无效") from exc
            preview_metadata = governance.build_knowledge_metadata(
                knowledge_id=knowledge_id,
                title=request.title,
                knowledge_type=request.type,
                layer=layer,
                scope=request.scope,
                actor=current_actor["id"],
                sources=request.source_references,
                tags=request.tags,
                technical_direction=request.technical_direction,
                owner_id=owner_id,
                created_at=created_at,
            )
            if claims.get("metadata_digest") != self._metadata_digest(
                preview_metadata,
                relative_path,
            ):
                raise ApiError(409, "preview_metadata_changed", "派生元数据已变更，请重新预览")
            existing = self.preview_nonces.lookup(
                jti=claims.get("jti"),
                actor=current_actor["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=relative_path,
            )
            if existing is not None and existing.get("status") in {"completed", "pending"}:
                result = existing.get("result")
                if existing.get("status") == "completed" and isinstance(result, dict):
                    return {**result, "idempotent_replay": True}
                recovered = self._recover_pending(existing, current_actor)
                if recovered is not None:
                    self.preview_nonces.complete(claims["jti"], recovered)
                    return {**recovered, "idempotent_replay": True}
                self.preview_tokens.ensure_not_expired(claims)
                raise ApiError(409, "preview_submission_in_progress", "该预览提交已在处理，请稍后重试")
            self.preview_tokens.ensure_not_expired(claims)
            body = f"# {request.title}\n\n{request.content}\n"
            self._preflight_checks(
                actor=current_actor,
                metadata=preview_metadata,
                body=body,
                relative_path=relative_path,
            )
            existing = self.preview_nonces.reserve(
                jti=claims.get("jti"),
                expires_at=claims.get("exp"),
                actor=current_actor["id"],
                form_digest=claims["form_digest"],
                knowledge_id=knowledge_id,
                relative_path=relative_path,
            )
            if existing is not None:  # lock makes this defensive rather than expected.
                raise ApiError(409, "preview_submission_in_progress", "该预览提交已在处理")
            try:
                metadata = governance.create_knowledge_entry(
                    repo=self.repo,
                    path=self.repo / relative_path,
                    knowledge_id=knowledge_id,
                    title=request.title,
                    knowledge_type=request.type,
                    layer=layer,
                    scope=request.scope,
                    sources=request.source_references,
                    content=request.content,
                    actor=current_actor["id"],
                    role=current_actor["role"],
                    tags=request.tags,
                    technical_direction=request.technical_direction,
                    owner_id=owner_id,
                    session="web:manual",
                    created_at=created_at,
                )
            except governance.GovernanceError as exc:
                self.preview_nonces.release(claims["jti"])
                message = str(exc)
                status = 409 if "已存在" in message else 422
                raise ApiError(status, "governance_write_failed", message) from exc
            except Exception:
                self.preview_nonces.release(claims["jti"])
                raise
            result = self._create_result(metadata, relative_path, current_actor)
            self.preview_nonces.complete(claims["jti"], result)
        return result

    def _create_result(
        self,
        metadata: Dict[str, Any],
        relative_path: str,
        actor: Dict[str, str],
    ) -> Dict[str, Any]:
        _layer, layer_root, _archived, _active = governance.layer_context(
            self.repo,
            self.repo / relative_path,
        )
        technical_direction = governance.entry_technical_direction(
            self.repo,
            self.repo / relative_path,
            metadata,
        )
        return {
            "knowledge": {
                "id": metadata["id"],
                "title": metadata["title"],
                "type": metadata["type"],
                "scope": governance.metadata_scope(metadata),
                "owner_id": metadata.get("owner_id"),
                "layer": metadata["layer"],
                "technical_direction": technical_direction,
                "maturity": metadata["maturity"],
                "created_at": metadata["created_at"],
                "tags": metadata.get("tags", []),
                "source_references": metadata.get("source_references", []),
                "relative_path": relative_path,
            },
            "actor": {
                "id": actor["id"],
                "display_name": actor["display_name"],
                "role": actor["role"],
            },
            "writes": [
                {
                    "key": "knowledge_file",
                    "label": "知识文件",
                    "status": "completed",
                    "detail": relative_path,
                },
                {
                    "key": "layer_catalog",
                    "label": "Layer B 分类目录",
                    "status": "completed",
                    "detail": (layer_root / "catalog.md").relative_to(self.repo).as_posix(),
                },
                {
                    "key": "global_catalog",
                    "label": "Layer A 全局目录",
                    "status": "completed",
                    "detail": "knowledge-catalog.md",
                },
                {
                    "key": "audit_log",
                    "label": "审计日志",
                    "status": "completed",
                    "detail": "log.md",
                },
            ],
            "catalog_updated": True,
            "audit_logged": True,
        }

    def _recover_pending(
        self,
        record: Dict[str, Any],
        actor: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        path = governance.resolve_inside(self.repo, record["relative_path"])
        if not path.exists() or not governance.is_entry_file(path):
            return None
        metadata, body = governance.read_entry(path)
        if metadata.get("id") != record.get("knowledge_id"):
            return None
        try:
            governance.require_valid_entry(self.repo, path, metadata, body)
        except governance.GovernanceError:
            return None
        if governance.catalog_issues(self.repo):
            return None
        log_path = self.repo / "log.md"
        if not log_path.is_file():
            return None
        audit_marker = (
            f"| `{record['actor']}` | `create` | `{metadata['id']}` | "
            f"{record['relative_path']} | `web:manual`"
        )
        if audit_marker not in log_path.read_text(encoding="utf-8"):
            return None
        return self._create_result(metadata, record["relative_path"], actor)

    @staticmethod
    def _content_without_title(metadata: Dict[str, Any], body: str) -> str:
        content = body.lstrip()
        heading = f"# {metadata['title']}"
        if content.startswith(heading):
            content = content[len(heading) :].lstrip("\r\n")
        return content.rstrip()

    def list_entries(
        self,
        actor: Dict[str, str],
        *,
        layer: Optional[KnowledgeLayer] = None,
        query: str = "",
    ) -> Dict[str, Any]:
        """List active knowledge for the human browser without recording evidence."""

        self.members.get_member(actor["id"])
        counts: Dict[str, int] = {
            "layer0p": 0,
            "layer1": 0,
            "layer2": 0,
            "layer3": 0,
        }
        normalized_query = query.strip().casefold()
        items: List[Dict[str, Any]] = []

        for path, metadata, body in governance.active_entries(self.repo):
            try:
                governance.require_valid_entry(self.repo, path, metadata, body)
            except governance.GovernanceError as exc:
                raise ApiError(409, "invalid_knowledge_entry", str(exc)) from exc

            entry_layer = str(metadata["layer"])
            counts[entry_layer] += 1
            if layer is not None and entry_layer != layer:
                continue

            content = self._content_without_title(metadata, body)
            tags = metadata.get("tags", [])
            technical_direction = governance.entry_technical_direction(
                self.repo,
                path,
                metadata,
            )
            searchable = " ".join(
                [
                    str(metadata["id"]),
                    str(metadata["title"]),
                    str(metadata["type"]),
                    str(technical_direction or ""),
                    str(metadata.get("owner_id") or ""),
                    " ".join(str(tag) for tag in tags),
                    content,
                ]
            ).casefold()
            if normalized_query and normalized_query not in searchable:
                continue

            excerpt = re.sub(r"\s+", " ", content).strip()
            if len(excerpt) > 180:
                excerpt = f"{excerpt[:180].rstrip()}…"
            items.append(
                {
                    "id": metadata["id"],
                    "title": metadata["title"],
                    "type": metadata["type"],
                    "scope": governance.metadata_scope(metadata),
                    "owner_id": metadata.get("owner_id"),
                    "layer": entry_layer,
                    "technical_direction": technical_direction,
                    "maturity": metadata["maturity"],
                    "created_at": metadata["created_at"],
                    "tags": tags,
                    "relative_path": path.relative_to(self.repo).as_posix(),
                    "excerpt": excerpt,
                }
            )

        items.sort(key=lambda item: (item["created_at"], item["id"]), reverse=True)
        return {"items": items, "counts": counts, "total": len(items)}

    def get_by_id(self, knowledge_id: str, actor: Dict[str, str]) -> Dict[str, Any]:
        """Return a repository-visible entry for the human completion UI only.

        This is not an Agent knowledge-consumption operation: it deliberately
        does not call ``require_consumption_access``, append reference evidence,
        change maturity, update catalogs, or write an audit event. Agent usage
        must continue through the governed reference workflow.
        """

        if not READABLE_ID_PATTERN.fullmatch(knowledge_id):
            raise ApiError(404, "knowledge_not_found", "知识不存在")
        matches: List[Tuple[Path, Dict[str, Any], str]] = []
        for path, metadata, body in governance.active_entries(self.repo):
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
        content = self._content_without_title(metadata, body)
        technical_direction = governance.entry_technical_direction(
            self.repo,
            path,
            metadata,
        )
        return {
            "knowledge": {
                "id": metadata["id"],
                "title": metadata["title"],
                "type": metadata["type"],
                "scope": governance.metadata_scope(metadata),
                "owner_id": metadata.get("owner_id"),
                "layer": metadata["layer"],
                "technical_direction": technical_direction,
                "maturity": metadata["maturity"],
                "created_at": metadata["created_at"],
                "tags": metadata.get("tags", []),
                "source_references": metadata.get("source_references", []),
                "relative_path": path.relative_to(self.repo).as_posix(),
                "content": content,
            }
        }
