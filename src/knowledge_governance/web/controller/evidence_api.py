from fastapi import APIRouter, Depends

from ..domain.models import CurrentUser
from ..domain.req import EvidenceCreateRequest
from ..middlewares.auth_dependency import get_current_user
from ..middlewares.auth_handler import require_local_user
from ..service.knowledge_service import KnowledgeService
from .dependencies import get_knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["evidence"])


@router.post("/{knowledge_id}/events")
def record_event(
    knowledge_id: str,
    data: EvidenceCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return service.record_event(knowledge_id, data, require_local_user(user))
