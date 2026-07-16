from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from backend.constant.enums import KnowledgeType, TechnicalDirection
from backend.exceptions.business_exception import ApiError
from backend.service.member_service import MemberService


TEMPLATE_FILES: Dict[KnowledgeType, str] = {
    "model": "model.md",
    "decision": "decision.md",
    "guideline": "guideline.md",
    "pitfall": "pitfall.md",
    "process": "process.md",
}

DIRECTION_TEMPLATE_FILES: Dict[TechnicalDirection, str] = {
    "patterns": "pattern.md",
    "anti-patterns": "anti-pattern.md",
}


class KnowledgeTemplateService:
    """Read the controlled Markdown examples used by the manual injection form."""

    def __init__(
        self,
        members: MemberService,
        template_dir: Path | None = None,
    ) -> None:
        self.members = members
        self.template_dir = (
            template_dir or Path(__file__).resolve().parents[1] / "template"
        )

    def get(
        self,
        knowledge_type: KnowledgeType,
        member: Dict[str, str],
        technical_direction: Optional[TechnicalDirection] = None,
    ) -> Dict[str, object]:
        self.members.require_role(member, "contributor", "maintainer", "super_admin")
        base_content = self._read(TEMPLATE_FILES[knowledge_type])
        content = base_content
        if technical_direction is not None:
            direction_content = self._read(
                DIRECTION_TEMPLATE_FILES[technical_direction]
            )
            content = f"{direction_content.rstrip()}\n\n{base_content.lstrip()}"
        return {
            "type": knowledge_type,
            "technical_direction": technical_direction,
            "content": content,
        }

    def _read(self, filename: str) -> str:
        template_path = self.template_dir / filename
        try:
            content = template_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ApiError(
                500,
                "knowledge_template_unavailable",
                "知识模板暂时无法加载，请稍后重试",
            ) from exc
        if not content.strip():
            raise ApiError(
                500,
                "knowledge_template_empty",
                "知识模板内容为空，请联系维护者",
            )
        return content
