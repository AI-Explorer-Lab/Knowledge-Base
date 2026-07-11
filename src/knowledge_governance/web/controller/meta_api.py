from fastapi import APIRouter

from ..constant.enums import EventType, KnowledgeScope, KnowledgeStatus, KnowledgeType, Maturity, Polarity, RiskLevel
from ..domain.req import COMMON_SECTIONS, TYPE_SECTIONS

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/form-options")
def form_options():
    return {
        "knowledge_types": [item.value for item in KnowledgeType],
        "scopes": [item.value for item in KnowledgeScope],
        "maturities": [item.value for item in Maturity],
        "statuses": [item.value for item in KnowledgeStatus],
        "risk_levels": [item.value for item in RiskLevel],
        "polarities": [item.value for item in Polarity],
        "event_types": [item.value for item in EventType],
        "phases": ["INIT", "ARCHITECT", "IMPLEMENT", "BUILD_VERIFY", "RELEASE", "ARCHIVE"],
        "common_sections": list(COMMON_SECTIONS),
        "type_sections": {key.value: list(value) for key, value in TYPE_SECTIONS.items()},
        "defaults": {"risk_level": "medium", "owner": "knowledge-core-team", "maturity": "draft", "status": "active"},
    }
