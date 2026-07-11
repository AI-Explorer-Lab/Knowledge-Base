from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..constant.enums import KnowledgeScope, KnowledgeType
from ..domain.models import CurrentUser
from ..domain.req import KnowledgeUpsertRequest
from ..domain.res import KnowledgeListResponse
from ..middlewares.auth_dependency import get_current_user
from ..middlewares.auth_handler import require_local_user
from ..service.knowledge_service import KnowledgeService
from .dependencies import get_knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=KnowledgeListResponse)
def list_knowledge(
    q: str = "",
    type: str = "",
    scope: str = "",
    status: str = "",
    service: KnowledgeService = Depends(get_knowledge_service),
):
    items = service.list_knowledge(q, type, scope, status)
    return {"items": items, "total": len(items)}


@router.get("/suggest-id")
def suggest_id(
    scope: KnowledgeScope = Query(...),
    type: KnowledgeType = Query(...),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return {"id": service.suggest_id(scope, type)}


@router.get("/{knowledge_id}")
def get_knowledge(knowledge_id: str, service: KnowledgeService = Depends(get_knowledge_service)):
    return service.get_knowledge(knowledge_id)


@router.post("/validate")
def validate_knowledge(
    data: KnowledgeUpsertRequest,
    existing_id: Optional[str] = None,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return {"ok": True, "preview": service.validate_knowledge(data, existing_id)}


@router.post("")
def create_knowledge(
    data: KnowledgeUpsertRequest,
    user: CurrentUser = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return service.create_knowledge(data, require_local_user(user))


@router.put("/{knowledge_id}")
def update_knowledge(
    knowledge_id: str,
    data: KnowledgeUpsertRequest,
    user: CurrentUser = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return service.update_knowledge(knowledge_id, data, require_local_user(user))
