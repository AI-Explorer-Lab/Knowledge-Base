from __future__ import annotations

from pathlib import Path
from typing import Dict

from backend.constant.enums import KnowledgeType
from backend.exceptions.business_exception import ApiError
from backend.service.member_service import MemberService


TEMPLATE_FILES: Dict[KnowledgeType, str] = {
    "model": "model.md",
    "decision": "decision.md",
    "guideline": "guideline.md",
    "pitfall": "pitfall.md",
    "process": "process.md",
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
    ) -> Dict[str, str]:
        self.members.require_role(member, "contributor", "maintainer")
        template_path = self.template_dir / TEMPLATE_FILES[knowledge_type]
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
        return {"type": knowledge_type, "content": content}
