from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..constant.enums import EventType, KnowledgeScope, KnowledgeType, Polarity, RiskLevel


COMMON_SECTIONS = ("结论", "背景与问题", "适用条件", "不适用条件", "详细说明", "验证方式", "来源")
TYPE_SECTIONS = {
    KnowledgeType.MODEL: ("实体或概念定义", "属性", "关系", "不变量", "权威来源"),
    KnowledgeType.DECISION: ("决策背景", "约束条件", "候选方案", "最终选择", "选择理由", "代价和后果", "重新决策条件"),
    KnowledgeType.GUIDELINE: ("具体行为", "预期收益", "例外情况"),
    KnowledgeType.PITFALL: ("触发条件", "问题现象", "根本原因", "复现方式", "规避或修复方法", "修复验证"),
    KnowledgeType.PROCESS: ("参与角色", "前置条件", "流程步骤", "状态转换", "异常分支", "权威确认人"),
}


class SourceReference(BaseModel):
    type: str = Field(min_length=1)
    ref: str = Field(min_length=1)


class ReviewOverride(BaseModel):
    interval: str = Field(pattern=r"^[1-9][0-9]*d$")
    reason: str = Field(min_length=1)


class KnowledgeUpsertRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = Field(default=None, pattern=r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
    title: str = Field(min_length=1, max_length=160)
    type: KnowledgeType
    scope: KnowledgeScope
    domain: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    risk_level: RiskLevel = RiskLevel.MEDIUM
    owner: str = Field(default="knowledge-core-team", min_length=1)
    maintainers: List[str] = Field(default_factory=list)
    applicable_phases: List[str] = Field(default_factory=list)
    applicable_conditions: List[str] = Field(min_length=1)
    not_applicable_conditions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source_references: List[SourceReference] = Field(min_length=1)
    polarity: Optional[Polarity] = None
    review_policy_override: Optional[ReviewOverride] = None
    sections: Dict[str, str]

    @model_validator(mode="after")
    def validate_type_fields(self):
        if self.type == KnowledgeType.GUIDELINE and self.polarity is None:
            raise ValueError("guideline 必须选择 polarity")
        required = COMMON_SECTIONS + TYPE_SECTIONS[self.type]
        missing = [name for name in required if not self.sections.get(name, "").strip()]
        if missing:
            raise ValueError("缺少正文内容：" + "、".join(missing))
        return self


class EvidenceCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: Optional[str] = None
    event_type: EventType
    occurred_at: Optional[dt.datetime] = None
    contributor: Optional[str] = None
    operator: Optional[str] = None
    project: Optional[str] = None
    scenario_id: Optional[str] = None
    evidence_group_id: Optional[str] = None
    validation_method: Optional[str] = None
    result_summary: Optional[str] = None
    reference: Optional[str] = None
    supersedes_event_id: Optional[str] = None
    revokes_event_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_evidence_fields(self):
        if self.event_type in {EventType.VALIDATED_SUCCESS, EventType.VALIDATED_FAILURE}:
            names = ("project", "scenario_id", "evidence_group_id", "validation_method", "result_summary", "reference")
            missing = [name for name in names if not getattr(self, name)]
            if missing:
                raise ValueError("验证事件缺少字段：" + "、".join(missing))
        return self
