from fastapi import APIRouter, Depends

from ..domain.models import CurrentUser
from ..middlewares.auth_dependency import get_current_user
from ..middlewares.auth_handler import require_local_user
from ..service.knowledge_service import KnowledgeService
from .dependencies import get_knowledge_service

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.post("/rebuild")
def rebuild(
    user: CurrentUser = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    require_local_user(user)
    return {"ok": True, "paths": service.rebuild_catalog()}
