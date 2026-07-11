from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .errors import KnowledgeError
from .models import EvidenceRecord, KnowledgeRecord
from .yaml_io import load_front_matter, load_yaml


KNOWLEDGE_ROOTS = ("team-conventions", "tech-wiki", "biz-wiki", "archive")


class Repository:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def knowledge_files(self) -> Iterable[Path]:
        for directory_name in KNOWLEDGE_ROOTS:
            directory = self.root / directory_name
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*.md")):
                if path.name.lower() in {"catalog.md", "readme.md"}:
                    continue
                yield path

    def load_knowledge(self) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        for path in self.knowledge_files():
            metadata, body = load_front_matter(path)
            records.append(KnowledgeRecord(path, metadata, body))
        return records

    def load_evidence(self) -> Dict[str, EvidenceRecord]:
        result: Dict[str, EvidenceRecord] = {}
        directory = self.root / "evidence"
        if not directory.exists():
            return result
        for path in sorted(directory.glob("*.yaml")):
            data = load_yaml(path, {})
            if not isinstance(data, dict):
                raise KnowledgeError(f"{path}: Evidence 必须是对象")
            knowledge_id = str(data.get("knowledge_id", ""))
            if knowledge_id in result:
                raise KnowledgeError(f"{path}: Evidence knowledge_id 重复：{knowledge_id}")
            result[knowledge_id] = EvidenceRecord(path, knowledge_id, data.get("events") or [])
        return result

    def config(self) -> dict:
        return load_yaml(self.root / ".knowledge-config.yaml", {}) or {}

    def policy(self, name: str) -> dict:
        return load_yaml(self.root / "policies" / f"{name}-policy.yaml", {}) or {}
