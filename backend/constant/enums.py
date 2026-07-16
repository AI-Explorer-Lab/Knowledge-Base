from typing import Literal


KnowledgeType = Literal["model", "decision", "guideline", "pitfall", "process"]
KnowledgeScope = Literal["personal", "team"]
KnowledgeLayer = Literal["layer0p", "layer0t", "layer1", "layer2", "layer3"]
KnowledgeMaturity = Literal["draft", "verified", "proven"]
TeamLayer = Literal["layer0t", "layer1", "layer2", "layer3"]
TechnicalDirection = Literal["patterns", "anti-patterns"]
AssignableMemberRole = Literal["reader", "contributor", "maintainer"]
MemberRole = Literal["reader", "contributor", "maintainer", "super_admin"]
MemberStatus = Literal["active", "disabled"]
BusinessDomainStatus = Literal["active", "disabled"]
