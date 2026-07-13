from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

from backend.constant.enums import (
    KnowledgeLayer,
    KnowledgeMaturity,
    KnowledgeScope,
    KnowledgeType,
    MemberRole,
    MemberStatus,
)


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OptionItem(ResponseModel):
    value: str
    label: str


class BusinessDomainResponse(ResponseModel):
    id: str
    name: str
    description: str


class KnowledgeOptionsResponse(ResponseModel):
    scopes: List[OptionItem]
    knowledge_types: List[OptionItem]
    layers: List[OptionItem]
    technical_directions: List[OptionItem]
    business_domains: List[BusinessDomainResponse]
    preview_ttl_seconds: int


class KnowledgeTemplateResponse(ResponseModel):
    type: KnowledgeType
    content: str


class MemberResponse(ResponseModel):
    id: str
    display_name: str
    role: MemberRole
    status: MemberStatus


class MeResponse(ResponseModel):
    member: MemberResponse
    permissions: Dict[str, bool]
    environment: str


class MembersResponse(ResponseModel):
    members: List[MemberResponse]


class MemberMutationResponse(ResponseModel):
    member: MemberResponse


class BusinessDomainMutationResponse(ResponseModel):
    business_domain: BusinessDomainResponse


class PreviewCheck(ResponseModel):
    key: str
    label: str
    status: Literal["passed", "failed"]
    detail: str


class PreviewResponse(ResponseModel):
    preview: Dict[str, Any]
    checks: List[PreviewCheck]
    preview_token: str
    expires_at: str


class CreatedKnowledge(ResponseModel):
    id: str
    title: str
    type: KnowledgeType
    scope: KnowledgeScope
    owner_id: Optional[str]
    layer: str
    maturity: Literal["draft"]
    created_at: str
    tags: List[str]
    source_references: List[str]
    relative_path: str


class ActorResponse(ResponseModel):
    id: str
    display_name: str
    role: MemberRole


class WriteResult(ResponseModel):
    key: str
    label: str
    status: Literal["completed"]
    detail: str


class CreateKnowledgeResponse(ResponseModel):
    knowledge: CreatedKnowledge
    actor: ActorResponse
    writes: List[WriteResult]
    catalog_updated: bool
    audit_logged: bool
    idempotent_replay: bool = False


class KnowledgeFileResponse(ResponseModel):
    knowledge: Dict[str, Any]


class KnowledgeListItem(ResponseModel):
    id: str
    title: str
    type: KnowledgeType
    scope: KnowledgeScope
    owner_id: Optional[str]
    layer: KnowledgeLayer
    maturity: KnowledgeMaturity
    created_at: str
    tags: List[str]
    relative_path: str
    excerpt: str


class KnowledgeListResponse(ResponseModel):
    items: List[KnowledgeListItem]
    counts: Dict[KnowledgeLayer, int]
    total: int


class HealthResponse(ResponseModel):
    status: Literal["ok", "degraded"]
    service: str
    database: Literal["ready", "unavailable"]
    repository: Literal["ready", "unavailable"]
