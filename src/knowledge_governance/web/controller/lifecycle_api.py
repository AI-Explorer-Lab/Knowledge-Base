import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends

from ..service.knowledge_service import KnowledgeService
from .dependencies import get_knowledge_service

router = APIRouter(prefix="/api/lifecycle", tags=["lifecycle"])


@router.get("/candidates")
def candidates(today: Optional[dt.date] = None, service: KnowledgeService = Depends(get_knowledge_service)):
    items = service.lifecycle_candidates(today)
    return {"items": items, "total": len(items)}
