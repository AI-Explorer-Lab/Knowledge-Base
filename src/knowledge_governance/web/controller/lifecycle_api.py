import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends

from ..domain.models import CurrentUser
from ..middlewares.auth_dependency import get_current_user
from ..middlewares.auth_handler import require_local_user
from ..service.knowledge_service import KnowledgeService
from .dependencies import get_knowledge_service

router = APIRouter(prefix="/api/lifecycle", tags=["lifecycle"])
knowledge_transition_router = APIRouter(prefix="/api/knowledge", tags=["lifecycle"])


@router.get("/candidates")
def candidates(today: Optional[dt.date] = None, service: KnowledgeService = Depends(get_knowledge_service)):
    items = service.lifecycle_candidates(today)
    return {"items": items, "total": len(items)}


@knowledge_transition_router.get("/{knowledge_id}/transition-options")
def transition_options(
    knowledge_id: str,
    today: Optional[dt.date] = None,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return service.transition_options(knowledge_id, today)


@knowledge_transition_router.post("/{knowledge_id}/transition-proposal")
def create_transition_proposal(
    knowledge_id: str,
    today: Optional[dt.date] = None,
    user: CurrentUser = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return service.create_transition_proposal(knowledge_id, require_local_user(user), today)
