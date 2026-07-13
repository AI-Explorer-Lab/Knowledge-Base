from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, Request

from backend.domain.res import MeResponse
from backend.middlewares.auth_dependency import current_member


router = APIRouter(prefix="/api", tags=["identity"])


@router.get("/me", response_model=MeResponse)
def get_me(request: Request, member: Dict[str, str] = Depends(current_member)) -> Dict:
    role = member["role"]
    return {
        "member": member,
        "permissions": {
            "can_create_knowledge": role in {"contributor", "maintainer"},
            "can_manage_members": role == "maintainer",
        },
        "environment": request.app.state.settings.environment_name,
    }
