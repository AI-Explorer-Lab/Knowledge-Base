from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ...models import KnowledgeRecord
from ...repository import Repository
from ...yaml_io import atomic_write, dump_yaml
from ..constant.enums import KnowledgeScope, KnowledgeType
from ..domain.req import COMMON_SECTIONS, TYPE_SECTIONS, KnowledgeUpsertRequest
from ..exceptions.business_exception import ConflictError, NotFoundError
from ..utils.markdown_sections import parse_sections, render_body


TYPE_CODES = {
    KnowledgeType.MODEL: "MOD",
    KnowledgeType.DECISION: "DEC",
    KnowledgeType.GUIDELINE: "GDL",
    KnowledgeType.PITFALL: "PIT",
    KnowledgeType.PROCESS: "PRC",
}
TYPE_DIRECTORIES = {
    KnowledgeType.MODEL: "models",
    KnowledgeType.DECISION: "decisions",
    KnowledgeType.GUIDELINE: "guidelines",
    KnowledgeType.PITFALL: "pitfalls",
    KnowledgeType.PROCESS: "processes",
}
SCOPE_PREFIXES = {
    KnowledgeScope.TEAM: "TM",
    KnowledgeScope.TECH: "TK",
    KnowledgeScope.BIZ: "BK",
    KnowledgeScope.PROJECT: "PK",
}


class FileKnowledgeMapper:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.repository = Repository(self.root)

    def list(self) -> List[KnowledgeRecord]:
        return self.repository.load_knowledge()

    def get(self, knowledge_id: str) -> KnowledgeRecord:
        for record in self.list():
            if record.id == knowledge_id:
                return record
        raise NotFoundError(f"知识不存在：{knowledge_id}")

    def suggest_id(self, scope: KnowledgeScope, knowledge_type: KnowledgeType) -> str:
        prefix = f"{SCOPE_PREFIXES[scope]}-{TYPE_CODES[knowledge_type]}-"
        values = []
        for record in self.list():
            match = re.fullmatch(re.escape(prefix) + r"([0-9]+)", record.id)
            if match:
                values.append(int(match.group(1)))
        return f"{prefix}{max(values, default=0) + 1:03d}"

    def target_path(self, data: KnowledgeUpsertRequest, knowledge_id: str) -> Path:
        if data.scope == KnowledgeScope.TEAM:
            return self.root / "team-conventions" / f"{knowledge_id}.md"
        if data.scope == KnowledgeScope.TECH:
            return self.root / "tech-wiki" / TYPE_DIRECTORIES[data.type] / f"{knowledge_id}.md"
        if data.scope == KnowledgeScope.BIZ:
            return self.root / "biz-wiki" / data.domain / TYPE_DIRECTORIES[data.type] / f"{knowledge_id}.md"
        return self.root / "docs" / "knowledge" / TYPE_DIRECTORIES[data.type] / f"{knowledge_id}.md"

    def build_record(self, data: KnowledgeUpsertRequest, existing: Optional[KnowledgeRecord] = None) -> KnowledgeRecord:
        today = dt.date.today().isoformat()
        knowledge_id = existing.id if existing else (data.id or self.suggest_id(data.scope, data.type))
        if existing:
            for field in ("type", "scope", "domain"):
                if data.model_dump(mode="json")[field] != existing.metadata.get(field):
                    raise ConflictError(f"编辑时不能直接修改 {field}；请通过重新分类提案处理")
        metadata = dict(existing.metadata) if existing else {}
        metadata.update({
            "schema_version": 1,
            "id": knowledge_id,
            "title": data.title,
            "type": data.type.value,
            "scope": data.scope.value,
            "domain": data.domain,
            "maturity": existing.metadata.get("maturity", "draft") if existing else "draft",
            "status": existing.metadata.get("status", "active") if existing else "active",
            "risk_level": data.risk_level.value,
            "owner": data.owner,
            "maintainers": sorted(set(data.maintainers)),
            "created_at": existing.metadata.get("created_at", today) if existing else today,
            "updated_at": today,
            "applicable_phases": sorted(set(data.applicable_phases)),
            "applicable_conditions": data.applicable_conditions,
            "not_applicable_conditions": data.not_applicable_conditions,
            "tags": sorted(set(data.tags)),
            "source_references": [item.model_dump(mode="json") for item in data.source_references],
            "supersedes": existing.metadata.get("supersedes", []) if existing else [],
            "superseded_by": existing.metadata.get("superseded_by") if existing else None,
        })
        if data.polarity:
            metadata["polarity"] = data.polarity.value
        if data.review_policy_override:
            metadata["review_policy_override"] = data.review_policy_override.model_dump(mode="json")
        ordered = COMMON_SECTIONS + TYPE_SECTIONS[data.type]
        body = render_body(data.title, data.sections, ordered)
        path = existing.path if existing else self.target_path(data, knowledge_id)
        return KnowledgeRecord(path, metadata, body)

    def write(self, record: KnowledgeRecord) -> None:
        text = "---\n" + dump_yaml(record.metadata) + "---\n" + record.body
        atomic_write(record.path, text)

    def as_detail(self, record: KnowledgeRecord) -> Dict[str, object]:
        return {
            "id": record.id,
            "path": str(record.path.relative_to(self.root)),
            "metadata": record.metadata,
            "sections": parse_sections(record.body),
        }
