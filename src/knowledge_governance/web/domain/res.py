from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ActionResponse(BaseModel):
    ok: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class KnowledgeListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
