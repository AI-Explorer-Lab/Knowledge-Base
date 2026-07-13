from typing import Literal


KnowledgeType = Literal["model", "decision", "guideline", "pitfall", "process"]
KnowledgeScope = Literal["personal", "team"]
KnowledgeLayer = Literal["layer0p", "layer1", "layer2", "layer3"]
KnowledgeMaturity = Literal["draft", "verified", "proven"]
TeamLayer = Literal["layer1", "layer2", "layer3"]
TechnicalDirection = Literal["patterns", "anti-patterns"]
MemberRole = Literal["reader", "contributor", "maintainer"]
MemberStatus = Literal["active", "disabled"]
