from __future__ import annotations

import json
from copy import deepcopy
from typing import Dict

from backend.domain.req import BusinessDomainCreate
from backend.exceptions.business_exception import ApiError
from backend.service.member_service import MemberService
from backend.service.repository_lock import RepositoryWriteLock


class BusinessDomainService:
    def __init__(
        self,
        members: MemberService,
        write_lock: RepositoryWriteLock,
    ) -> None:
        self.members = members
        self.write_lock = write_lock

    def create(
        self,
        actor: Dict[str, str],
        request: BusinessDomainCreate,
    ) -> Dict[str, str]:
        with self.write_lock.acquire():
            current_actor = self.members.get_member(actor["id"])
            self.members.require_role(current_actor, "maintainer")
            config = self.members.load_config()
            configured = config["knowledge_options"].get("business_domains", [])
            normalized = self.members.normalize_business_domains(configured)
            if any(item["id"] == request.id for item in normalized):
                raise ApiError(
                    409,
                    "business_domain_exists",
                    f"业务领域标识已存在：{request.id}",
                    field_errors={"id": "请使用其他领域标识"},
                )

            domain = request.model_dump()
            config["knowledge_options"]["business_domains"] = [*normalized, domain]
            self.members.write_config_and_audit(
                config,
                actor_id=current_actor["id"],
                action="business-domain-create",
                target_id=domain["id"],
                detail=json.dumps(
                    {"after": domain},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                session="web:business-domains",
            )
            return deepcopy(domain)
