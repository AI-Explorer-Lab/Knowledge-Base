from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.constant.enums import (
    AssignableMemberRole,
    BusinessDomainStatus,
    KnowledgeScope,
    KnowledgeType,
    MemberStatus,
    TeamLayer,
    TechnicalDirection,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KnowledgeInput(StrictModel):
    scope: KnowledgeScope
    title: str = Field(min_length=1, max_length=160)
    type: KnowledgeType
    tags: List[str] = Field(default_factory=list, max_length=20)
    source_references: List[str] = Field(min_length=1, max_length=20)
    layer: Optional[TeamLayer] = None
    technical_direction: Optional[TechnicalDirection] = None
    domain: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=48,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    content: str = Field(min_length=1, max_length=200_000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("标题不能包含控制字符或换行")
        return value

    @field_validator("tags", "source_references")
    @classmethod
    def normalize_string_lists(cls, value: List[str]) -> List[str]:
        result: List[str] = []
        for item in value:
            normalized = item.strip()
            if not normalized:
                raise ValueError("不允许空值")
            if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
                raise ValueError("标签和来源不能包含控制字符或换行")
            if len(normalized) > 200:
                raise ValueError("单项长度不能超过 200 字符")
            if normalized not in result:
                result.append(normalized)
        return result

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("知识正文不能为空")
        if "\x00" in value:
            raise ValueError("知识正文不能包含空字符")
        return value

    @model_validator(mode="after")
    def validate_scope_fields(self) -> "KnowledgeInput":
        if self.scope == "personal":
            if self.layer is not None:
                raise ValueError("个人知识的层级由后端固定为 layer0p")
            if self.technical_direction is not None:
                raise ValueError("个人知识不能指定技术知识方向")
            if self.domain is not None:
                raise ValueError("个人知识不能指定业务领域")
        else:
            if self.layer is None:
                raise ValueError("团队知识必须选择层级")
            if self.layer != "layer1" and self.technical_direction is not None:
                raise ValueError("只有 Layer 1 知识可以指定技术立场标签")
            if self.layer == "layer2" and self.domain is None:
                raise ValueError("Layer 2 知识必须选择业务领域")
            if self.layer != "layer2" and self.domain is not None:
                raise ValueError("只有 Layer 2 知识可以指定业务领域")
        return self


class ManualKnowledgeRequest(KnowledgeInput):
    preview_token: str = Field(min_length=20, max_length=8192)


class BusinessDomainCreate(StrictModel):
    id: str = Field(
        min_length=1,
        max_length=48,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=240)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if value == "archive":
            raise ValueError("archive 是保留标识，不能作为业务领域")
        return value

    @field_validator("name", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("业务领域信息不能包含控制字符或换行")
        return value


class BusinessDomainPatch(StrictModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=240)
    status: Optional[BusinessDomainStatus] = None

    @field_validator("name", "description")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and any(
            ord(character) < 32 or ord(character) == 127 for character in value
        ):
            raise ValueError("业务领域信息不能包含控制字符或换行")
        return value

    @model_validator(mode="after")
    def require_change(self) -> "BusinessDomainPatch":
        if self.name is None and self.description is None and self.status is None:
            raise ValueError("至少提供一个要修改的字段")
        return self


class MemberCreate(StrictModel):
    id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    display_name: str = Field(min_length=1, max_length=80)
    role: AssignableMemberRole

    @field_validator("id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return value.lower()

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("显示名称不能包含控制字符或换行")
        return value


class MemberPatch(StrictModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    role: Optional[AssignableMemberRole] = None
    status: Optional[MemberStatus] = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and any(
            ord(character) < 32 or ord(character) == 127 for character in value
        ):
            raise ValueError("显示名称不能包含控制字符或换行")
        return value

    @model_validator(mode="after")
    def require_change(self) -> "MemberPatch":
        if self.display_name is None and self.role is None and self.status is None:
            raise ValueError("至少提供一个要修改的字段")
        return self


class SuperAdminKnowledgeInput(StrictModel):
    scope: KnowledgeScope
    owner_id: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$",
    )
    title: str = Field(min_length=1, max_length=160)
    type: KnowledgeType
    tags: List[str] = Field(default_factory=list, max_length=20)
    source_references: List[str] = Field(min_length=1, max_length=20)
    layer: Optional[TeamLayer] = None
    technical_direction: Optional[TechnicalDirection] = None
    domain: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=48,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    content: str = Field(min_length=1, max_length=200_000)
    reason: str = Field(min_length=3, max_length=500)
    base_digest: str = Field(min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$")
    owner_confirmed_by: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$",
    )

    @field_validator("title", "reason")
    @classmethod
    def validate_single_line(cls, value: str) -> str:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("标题和修改原因不能包含控制字符或换行")
        return value

    @field_validator("tags", "source_references")
    @classmethod
    def normalize_string_lists(cls, value: List[str]) -> List[str]:
        result: List[str] = []
        for item in value:
            normalized = item.strip()
            if not normalized:
                raise ValueError("不允许空值")
            if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
                raise ValueError("标签和来源不能包含控制字符或换行")
            if len(normalized) > 200:
                raise ValueError("单项长度不能超过 200 字符")
            if normalized not in result:
                result.append(normalized)
        return result

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("知识正文不能为空")
        if "\x00" in value:
            raise ValueError("知识正文不能包含空字符")
        return value

    @model_validator(mode="after")
    def validate_destination(self) -> "SuperAdminKnowledgeInput":
        if self.scope == "personal":
            if not self.owner_id:
                raise ValueError("个人知识必须指定所有者")
            if self.layer is not None or self.technical_direction is not None or self.domain is not None:
                raise ValueError("个人知识不能指定团队层级、技术方向或业务领域")
        else:
            if self.owner_id is not None:
                raise ValueError("团队知识不能指定个人所有者")
            if self.layer is None:
                raise ValueError("团队知识必须选择层级")
            if self.layer != "layer1" and self.technical_direction is not None:
                raise ValueError("只有 Layer 1 知识可以指定技术方向")
            if self.layer == "layer2" and self.domain is None:
                raise ValueError("Layer 2 知识必须选择业务领域")
            if self.layer != "layer2" and self.domain is not None:
                raise ValueError("只有 Layer 2 知识可以指定业务领域")
        return self


class SuperAdminKnowledgeCommit(SuperAdminKnowledgeInput):
    preview_token: str = Field(min_length=20, max_length=8192)


class SuperAdminKnowledgeAction(StrictModel):
    action: Literal[
        "approve_proven",
        "propose_promotion",
        "approve_promotion",
        "rollback_layer",
        "archive",
        "restore",
        "mark_conflict",
        "resolve_conflict",
    ]
    reason: str = Field(min_length=3, max_length=500)
    target_layer: Optional[Literal["layer1", "layer2"]] = None
    domain: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=48,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    owner_confirmed_by: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("操作原因不能包含控制字符或换行")
        return value

    @model_validator(mode="after")
    def validate_action_fields(self) -> "SuperAdminKnowledgeAction":
        if self.action == "propose_promotion" and self.target_layer is None:
            raise ValueError("发起层级提升必须选择目标层级")
        if self.target_layer == "layer2" and self.domain is None:
            raise ValueError("提升到 Layer 2 必须选择业务领域")
        if self.target_layer != "layer2" and self.domain is not None:
            raise ValueError("只有提升到 Layer 2 时可以指定业务领域")
        return self
