from __future__ import annotations

from typing import Dict, Literal, Optional

from fastapi import APIRouter, Depends, Query, Request

from backend.constant.enums import KnowledgeLayer, KnowledgeMaturity, KnowledgeScope
from backend.domain.req import (
    SuperAdminKnowledgeAction,
    SuperAdminKnowledgeCommit,
    SuperAdminKnowledgeInput,
)
from backend.domain.res import (
    AuditListResponse,
    SuperAdminActionResponse,
    SuperAdminCommitResponse,
    SuperAdminKnowledgeDetailResponse,
    SuperAdminKnowledgeListResponse,
    SuperAdminPreviewResponse,
)
from backend.middlewares.auth_dependency import current_member
from backend.service.super_admin_service import SuperAdminService


router = APIRouter(prefix="/api/super-admin", tags=["super-admin"])


def super_admin_service(request: Request) -> SuperAdminService:
    return request.app.state.super_admin


@router.get("/knowledge", response_model=SuperAdminKnowledgeListResponse)
def list_knowledge(
    state: Literal["active", "archived", "all"] = Query(default="active"),
    layer: Optional[KnowledgeLayer] = Query(default=None),
    scope: Optional[KnowledgeScope] = Query(default=None),
    maturity: Optional[KnowledgeMaturity] = Query(default=None),
    q: str = Query(default="", max_length=100),
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.list_entries(
        member,
        state=state,
        layer=layer,
        scope=scope,
        maturity=maturity,
        query=q,
    )


@router.get("/knowledge/{knowledge_id}", response_model=SuperAdminKnowledgeDetailResponse)
def get_knowledge(
    knowledge_id: str,
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.get_entry(member, knowledge_id)


@router.post(
    "/knowledge/{knowledge_id}/preview",
    response_model=SuperAdminPreviewResponse,
)
def preview_knowledge_update(
    knowledge_id: str,
    payload: SuperAdminKnowledgeInput,
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.preview(member, knowledge_id, payload)


@router.post(
    "/knowledge/{knowledge_id}/commit",
    response_model=SuperAdminCommitResponse,
)
def commit_knowledge_update(
    request: Request,
    knowledge_id: str,
    payload: SuperAdminKnowledgeCommit,
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.commit(
        member,
        knowledge_id,
        payload,
        getattr(request.state, "request_id", "unknown"),
    )


@router.post(
    "/knowledge/{knowledge_id}/actions",
    response_model=SuperAdminActionResponse,
)
def execute_knowledge_action(
    request: Request,
    knowledge_id: str,
    payload: SuperAdminKnowledgeAction,
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.action(
        member,
        knowledge_id,
        payload,
        getattr(request.state, "request_id", "unknown"),
    )


@router.get("/audit", response_model=AuditListResponse)
def list_audit(
    q: str = Query(default="", max_length=100),
    action: str = Query(default="", max_length=80),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    member: Dict[str, str] = Depends(current_member),
    service: SuperAdminService = Depends(super_admin_service),
) -> Dict:
    return service.audit(member, query=q, action=action, offset=offset, limit=limit)
