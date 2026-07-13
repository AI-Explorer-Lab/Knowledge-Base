from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from backend.constant.enums import KnowledgeLayer, KnowledgeType, TechnicalDirection
from backend.domain.req import KnowledgeInput, ManualKnowledgeRequest
from backend.domain.res import (
    CreateKnowledgeResponse,
    KnowledgeFileResponse,
    KnowledgeListResponse,
    KnowledgeOptionsResponse,
    KnowledgeTemplateResponse,
    PreviewResponse,
)
from backend.middlewares.auth_dependency import current_member
from backend.service.knowledge_service import KnowledgeService
from backend.service.knowledge_template_service import KnowledgeTemplateService


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def knowledge_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge


def knowledge_template_service(request: Request) -> KnowledgeTemplateService:
    return request.app.state.knowledge_templates


@router.get("/options", response_model=KnowledgeOptionsResponse)
def get_options(
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeService = Depends(knowledge_service),
) -> Dict:
    service.members.require_role(member, "contributor", "maintainer")
    return service.options()


@router.get(
    "/templates/{knowledge_type}",
    response_model=KnowledgeTemplateResponse,
)
def get_template(
    knowledge_type: KnowledgeType,
    technical_direction: Optional[TechnicalDirection] = Query(default=None),
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeTemplateService = Depends(knowledge_template_service),
) -> Dict:
    return service.get(knowledge_type, member, technical_direction)


@router.post("/preview", response_model=PreviewResponse)
def preview_knowledge(
    payload: KnowledgeInput,
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeService = Depends(knowledge_service),
) -> Dict:
    return service.preview(payload, member)


@router.post(
    "/manual",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateKnowledgeResponse,
)
def create_knowledge(
    payload: ManualKnowledgeRequest,
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeService = Depends(knowledge_service),
) -> Dict:
    return service.create(payload, member)


@router.get("", response_model=KnowledgeListResponse)
def list_knowledge(
    layer: Optional[KnowledgeLayer] = Query(default=None),
    q: str = Query(default="", max_length=100),
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeService = Depends(knowledge_service),
) -> Dict:
    return service.list_entries(member, layer=layer, query=q)


@router.get("/{knowledge_id}", response_model=KnowledgeFileResponse)
def get_knowledge(
    knowledge_id: str,
    member: Dict[str, str] = Depends(current_member),
    service: KnowledgeService = Depends(knowledge_service),
) -> Dict:
    # Human view-only endpoint for the completion modal. It is not an Agent
    # consumption/reference call and therefore must remain evidence-neutral.
    return service.get_by_id(knowledge_id, member)
