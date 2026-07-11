from enum import Enum


class KnowledgeType(str, Enum):
    MODEL = "model"
    DECISION = "decision"
    GUIDELINE = "guideline"
    PITFALL = "pitfall"
    PROCESS = "process"


class KnowledgeScope(str, Enum):
    TEAM = "team"
    TECH = "tech"
    BIZ = "biz"


class Maturity(str, Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    PROVEN = "proven"


class KnowledgeStatus(str, Enum):
    ACTIVE = "active"
    REVIEW_DUE = "review_due"
    DISPUTED = "disputed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Polarity(str, Enum):
    RECOMMEND = "recommend"
    AVOID = "avoid"


class EventType(str, Enum):
    REFERENCED = "referenced"
    ADOPTED = "adopted"
    VALIDATED_SUCCESS = "validated_success"
    VALIDATED_FAILURE = "validated_failure"
    NOT_APPLICABLE = "not_applicable"
    CONTRADICTION_FOUND = "contradiction_found"
    REVIEW_COMPLETED = "review_completed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    EVENT_CORRECTION = "event_correction"
    EVENT_REVOKED = "event_revoked"
