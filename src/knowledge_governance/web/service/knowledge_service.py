from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...catalog import build_catalogs
from ...evidence import append_event, utc_now
from ...lifecycle import derived_dates, evaluate
from ...models import KnowledgeRecord
from ...repository import Repository
from ...validator import validate
from ..constant.enums import KnowledgeScope, KnowledgeType
from ..domain.models import CurrentUser
from ..domain.req import EvidenceCreateRequest, KnowledgeUpsertRequest
from ..exceptions.business_exception import BusinessException, ConflictError
from ..mapper.file_knowledge_mapper import FileKnowledgeMapper


class KnowledgeService:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.mapper = FileKnowledgeMapper(self.root)
        self.repository = Repository(self.root)

    def _validate_candidate(self, candidate: KnowledgeRecord, replacing_id: Optional[str] = None) -> None:
        records = [record for record in self.mapper.list() if record.id != replacing_id]
        findings = validate(self.root, records + [candidate], self.repository.load_evidence())
        errors = [finding.render() for finding in findings if finding.severity == "error"]
        if errors:
            raise BusinessException("；".join(errors), 422, "VALIDATION_FAILED")

    def list_knowledge(self, query: str = "", knowledge_type: str = "", scope: str = "", status: str = "") -> List[Dict[str, Any]]:
        evidence = self.repository.load_evidence()
        review_policy = self.repository.policy("review")
        result = []
        for record in self.mapper.list():
            metadata = record.metadata
            haystack = f"{record.id} {metadata.get('title', '')} {' '.join(metadata.get('tags') or [])}".lower()
            if query and query.lower() not in haystack:
                continue
            if knowledge_type and metadata.get("type") != knowledge_type:
                continue
            if scope and metadata.get("scope") != scope:
                continue
            if status and metadata.get("status") != status:
                continue
            events = evidence.get(record.id).events if record.id in evidence else []
            result.append({
                "id": record.id,
                "title": metadata["title"],
                "type": metadata["type"],
                "scope": metadata["scope"],
                "domain": metadata["domain"],
                "maturity": metadata["maturity"],
                "status": metadata["status"],
                "risk_level": metadata["risk_level"],
                "owner": metadata["owner"],
                "path": str(record.path.relative_to(self.root)),
                "derived": derived_dates(metadata, events, review_policy),
            })
        return sorted(result, key=lambda item: item["id"])

    def get_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        record = self.mapper.get(knowledge_id)
        detail = self.mapper.as_detail(record)
        evidence = self.repository.load_evidence().get(knowledge_id)
        detail["events"] = evidence.events if evidence else []
        detail["derived"] = derived_dates(record.metadata, detail["events"], self.repository.policy("review"))
        return detail

    def suggest_id(self, scope: KnowledgeScope, knowledge_type: KnowledgeType) -> str:
        return self.mapper.suggest_id(scope, knowledge_type)

    def validate_knowledge(self, data: KnowledgeUpsertRequest, existing_id: Optional[str] = None) -> Dict[str, Any]:
        existing = self.mapper.get(existing_id) if existing_id else None
        candidate = self.mapper.build_record(data, existing)
        self._validate_candidate(candidate, existing_id)
        return self.mapper.as_detail(candidate)

    def create_knowledge(self, data: KnowledgeUpsertRequest, user: CurrentUser) -> Dict[str, Any]:
        candidate = self.mapper.build_record(data)
        if any(record.id == candidate.id for record in self.mapper.list()) or candidate.path.exists():
            raise ConflictError(f"知识 ID 或目标路径已经存在：{candidate.id}")
        self._validate_candidate(candidate)
        self.mapper.write(candidate)
        self._append_log(f"knowledge create {candidate.id} by {user.id}")
        self.rebuild_catalog()
        return self.get_knowledge(candidate.id)

    def update_knowledge(self, knowledge_id: str, data: KnowledgeUpsertRequest, user: CurrentUser) -> Dict[str, Any]:
        existing = self.mapper.get(knowledge_id)
        if data.id and data.id != knowledge_id:
            raise ConflictError("编辑时不能修改知识 ID")
        candidate = self.mapper.build_record(data, existing)
        self._validate_candidate(candidate, knowledge_id)
        self.mapper.write(candidate)
        self._append_log(f"knowledge update {knowledge_id} by {user.id}")
        self.rebuild_catalog()
        return self.get_knowledge(knowledge_id)

    def record_event(self, knowledge_id: str, data: EvidenceCreateRequest, user: CurrentUser) -> Dict[str, Any]:
        self.mapper.get(knowledge_id)
        payload = data.model_dump(mode="json", exclude_none=True)
        payload["event_type"] = data.event_type.value
        payload["event_id"] = data.event_id or f"EVT-{uuid.uuid4().hex[:16].upper()}"
        payload["occurred_at"] = data.occurred_at.isoformat() if data.occurred_at else utc_now()
        payload["contributor"] = data.contributor or f"user:{user.id}"
        created = append_event(self.root, knowledge_id, payload)
        self.rebuild_catalog()
        return {"created": created, "event": payload}

    def lifecycle_candidates(self, today: Optional[dt.date] = None) -> List[Dict[str, Any]]:
        evidence = self.repository.load_evidence()
        review = self.repository.policy("review")
        maturity = self.repository.policy("maturity")
        result = []
        for record in self.mapper.list():
            events = evidence.get(record.id).events if record.id in evidence else []
            proposals = evaluate(record.metadata, events, review, maturity, today or dt.date.today())
            if proposals:
                result.append({"knowledge_id": record.id, "title": record.metadata["title"], "proposals": proposals, "derived": derived_dates(record.metadata, events, review)})
        return result

    def rebuild_catalog(self) -> List[str]:
        paths = build_catalogs(self.root, self.mapper.list(), self.repository.load_evidence(), self.repository.policy("review"))
        return [str(path.relative_to(self.root)) for path in paths]

    def _append_log(self, message: str) -> None:
        timestamp = utc_now()
        with (self.root / "log.md").open("a", encoding="utf-8") as handle:
            handle.write(f"- {timestamp} {message}\n")
