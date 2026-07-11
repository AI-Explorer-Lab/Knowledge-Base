from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class KnowledgeRecord:
    path: Path
    metadata: Dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        return str(self.metadata.get("id", ""))


@dataclass(frozen=True)
class EvidenceRecord:
    path: Path
    knowledge_id: str
    events: List[Dict[str, Any]]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str

    def render(self) -> str:
        return f"{self.severity.upper():7} {self.path}: {self.message}"
