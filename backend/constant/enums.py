from typing import Literal


KnowledgeType = Literal["model", "decision", "guideline", "pitfall", "process"]
KnowledgeScope = Literal["personal", "team"]
TeamLayer = Literal["layer1", "layer2", "layer3"]
MemberRole = Literal["reader", "contributor", "maintainer"]
MemberStatus = Literal["active", "disabled"]
