from __future__ import annotations

import json
from copy import deepcopy
from typing import Dict

from backend.domain.req import BusinessDomainCreate, BusinessDomainPatch
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
            self.members.require_role(current_actor, "maintainer", "super_admin")
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

            domain = {**request.model_dump(), "status": "active"}
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

    def patch(
        self,
        actor: Dict[str, str],
        domain_id: str,
        request: BusinessDomainPatch,
    ) -> Dict[str, str]:
        with self.write_lock.acquire():
            current_actor = self.members.get_member(actor["id"])
            self.members.require_role(current_actor, "super_admin")
            config = self.members.load_config()
            normalized = self.members.normalize_business_domains(
                config["knowledge_options"].get("business_domains", [])
            )
            target = next((item for item in normalized if item["id"] == domain_id), None)
            if target is None:
                raise ApiError(404, "business_domain_not_found", "业务领域不存在")
            before = deepcopy(target)
            target.update(request.model_dump(exclude_none=True))
            if target != before:
                config["knowledge_options"]["business_domains"] = normalized
                self.members.write_config_and_audit(
                    config,
                    actor_id=current_actor["id"],
                    action="business-domain-update",
                    target_id=domain_id,
                    detail=json.dumps(
                        {"before": before, "after": target},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    session="web:business-domains",
                )
            return deepcopy(target)
