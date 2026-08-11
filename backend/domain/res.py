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
    TechnicalDirection,
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
    status: Literal["active", "disabled"] = "active"


class KnowledgeOptionsResponse(ResponseModel):
    scopes: List[OptionItem]
    knowledge_types: List[OptionItem]
    layers: List[OptionItem]
    technical_directions: List[OptionItem]
    business_domains: List[BusinessDomainResponse]
    preview_ttl_seconds: int


class KnowledgeTemplateResponse(ResponseModel):
    type: KnowledgeType
    technical_direction: Optional[TechnicalDirection]
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
    layer: KnowledgeLayer
    technical_direction: Optional[TechnicalDirection]
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


class KnowledgeReviewResponse(ResponseModel):
    next_review_at: str
    overdue: bool


class KnowledgeFileItem(ResponseModel):
    id: str
    title: str
    type: KnowledgeType
    scope: KnowledgeScope
    owner_id: Optional[str]
    layer: KnowledgeLayer
    technical_direction: Optional[TechnicalDirection]
    maturity: KnowledgeMaturity
    created_at: str
    tags: List[str]
    source_references: List[str]
    relative_path: str
    content: str
    review: KnowledgeReviewResponse


class KnowledgeFileResponse(ResponseModel):
    knowledge: KnowledgeFileItem


class MaturityEvidenceResponse(ResponseModel):
    kind: Literal["reference", "validation"]
    occurred_at: str
    revision: int
    contributor: Optional[str] = None
    project_id: Optional[str] = None
    workflow_id: Optional[str] = None
    used_in: Optional[str] = None
    result: Optional[Literal["passed", "failed"]] = None
    source: Optional[str] = None


class MaturityHistoryEventResponse(ResponseModel):
    occurred_at: str
    event_type: Literal[
        "created",
        "revision_reset",
        "referenced",
        "validated",
        "maturity_changed",
        "decayed",
        "restored",
    ]
    from_maturity: Optional[KnowledgeMaturity] = None
    to_maturity: Optional[KnowledgeMaturity] = None
    revision: Optional[int] = None
    actor: Optional[str] = None
    summary: str
    reason: Optional[str] = None
    changed_fields: List[str]
    evidence: List[MaturityEvidenceResponse]
    data_source: Literal["metadata", "audit", "legacy_audit"]


class MaturityHistoryResponse(ResponseModel):
    current_maturity: KnowledgeMaturity
    current_revision: int
    events: List[MaturityHistoryEventResponse]


class SuperAdminKnowledgeListResponse(ResponseModel):
    items: List[Dict[str, Any]]
    counts: Dict[str, int]
    total: int


class SuperAdminKnowledgeDetailResponse(ResponseModel):
    knowledge: Dict[str, Any]


class SuperAdminPreviewResponse(ResponseModel):
    before: Dict[str, Any]
    after: Dict[str, Any]
    changed_fields: List[str]
    consequences: List[str]
    checks: List[PreviewCheck]
    preview_token: str
    expires_at: str


class SuperAdminCommitResponse(ResponseModel):
    knowledge: Dict[str, Any]
    writes: List[WriteResult]
    audit_logged: bool
    idempotent_replay: bool = False


class SuperAdminActionResponse(ResponseModel):
    knowledge: Dict[str, Any]
    action: str
    audit_logged: bool


class AuditRecordResponse(ResponseModel):
    timestamp: str
    actor: str
    action: str
    target_id: str
    detail: Any
    session: str


class AuditListResponse(ResponseModel):
    items: List[AuditRecordResponse]
    total: int


class KnowledgeListItem(ResponseModel):
    id: str
    title: str
    type: KnowledgeType
    scope: KnowledgeScope
    owner_id: Optional[str]
    layer: KnowledgeLayer
    technical_direction: Optional[TechnicalDirection]
    maturity: KnowledgeMaturity
    created_at: str
    tags: List[str]
    relative_path: str
    excerpt: str
    review: KnowledgeReviewResponse


class KnowledgeListResponse(ResponseModel):
    items: List[KnowledgeListItem]
    counts: Dict[KnowledgeLayer, int]
    total: int


class HealthResponse(ResponseModel):
    status: Literal["ok", "degraded"]
    service: str
    database: Literal["ready", "unavailable"]
    repository: Literal["ready", "unavailable"]
