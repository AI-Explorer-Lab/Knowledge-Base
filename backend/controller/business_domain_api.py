from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, Request, status

from backend.domain.req import BusinessDomainCreate
from backend.domain.res import BusinessDomainMutationResponse
from backend.middlewares.auth_dependency import current_member
from backend.service.business_domain_service import BusinessDomainService


router = APIRouter(prefix="/api/business-domains", tags=["business-domains"])


def business_domain_service(request: Request) -> BusinessDomainService:
    return request.app.state.business_domains


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BusinessDomainMutationResponse,
)
def create_business_domain(
    payload: BusinessDomainCreate,
    member: Dict[str, str] = Depends(current_member),
    service: BusinessDomainService = Depends(business_domain_service),
) -> Dict:
    return {"business_domain": service.create(member, payload)}
