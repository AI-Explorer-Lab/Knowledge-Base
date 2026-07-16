from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, Request, status

from backend.domain.req import MemberCreate, MemberPatch
from backend.domain.res import MemberMutationResponse, MembersResponse
from backend.middlewares.auth_dependency import current_member
from backend.service.member_service import MemberService


router = APIRouter(prefix="/api/members", tags=["members"])


def member_service(request: Request) -> MemberService:
    return request.app.state.members


@router.get("", response_model=MembersResponse)
def list_members(
    member: Dict[str, str] = Depends(current_member),
    service: MemberService = Depends(member_service),
) -> Dict:
    service.require_role(member, "maintainer", "super_admin")
    return {"members": service.list_members()}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MemberMutationResponse)
def create_member(
    payload: MemberCreate,
    member: Dict[str, str] = Depends(current_member),
    service: MemberService = Depends(member_service),
) -> Dict:
    return {"member": service.create_member(member, payload)}


@router.patch("/{member_id}", response_model=MemberMutationResponse)
def patch_member(
    member_id: str,
    payload: MemberPatch,
    member: Dict[str, str] = Depends(current_member),
    service: MemberService = Depends(member_service),
) -> Dict:
    return {"member": service.patch_member(member, member_id, payload)}
