from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class KnowledgeTarget:
    """HTTP-independent, server-derived destination for one knowledge entry."""

    relative_path: str
    layer: str
    owner_id: Optional[str]
