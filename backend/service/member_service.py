from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import yaml

from tools import knowledge_governance as governance
from backend.domain.req import MemberCreate, MemberPatch
from backend.exceptions.business_exception import ApiError
from backend.service.repository_lock import RepositoryWriteLock


MEMBER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
SAFE_SEGMENT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
MEMBER_ROLES = {"reader", "contributor", "maintainer"}
MEMBER_STATUSES = {"active", "disabled"}
LAYERS = {"layer0p", "layer1", "layer2", "layer3"}


class MemberService:
    def __init__(self, repo: Path, write_lock: RepositoryWriteLock) -> None:
        self.repo = repo.resolve()
        self.path = self.repo / ".knowledge-config.yaml"
        self.write_lock = write_lock

    def _configuration_error(self, message: str) -> ApiError:
        return ApiError(500, "invalid_configuration", message)

    def load_config(self) -> Dict[str, Any]:
        try:
            raw = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise self._configuration_error("缺少 .knowledge-config.yaml") from exc
        except (OSError, yaml.YAMLError) as exc:
            raise self._configuration_error(f"无法读取成员配置：{exc}") from exc
        if not isinstance(raw, dict):
            raise self._configuration_error("成员配置必须是 YAML 对象")
        if raw.get("version") != 1:
            raise self._configuration_error("成员配置 version 必须为 1")

        members = raw.get("members")
        if not isinstance(members, list):
            raise self._configuration_error("members 必须是数组")
        seen = set()
        active_maintainers = 0
        for index, member in enumerate(members):
            if not isinstance(member, dict):
                raise self._configuration_error(f"members[{index}] 必须是对象")
            member_id = member.get("id")
            if not isinstance(member_id, str) or not MEMBER_ID_PATTERN.fullmatch(member_id):
                raise self._configuration_error(f"members[{index}].id 格式无效")
            normalized_member_id = member_id.casefold()
            if normalized_member_id in seen:
                raise self._configuration_error(f"成员 ID 重复：{member_id}")
            seen.add(normalized_member_id)
            display_name = member.get("display_name")
            if (
                not isinstance(display_name, str)
                or not display_name.strip()
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in display_name
                )
            ):
                raise self._configuration_error(f"members[{index}].display_name 格式无效")
            if member.get("role") not in MEMBER_ROLES:
                raise self._configuration_error(f"members[{index}].role 格式无效")
            if member.get("status") not in MEMBER_STATUSES:
                raise self._configuration_error(f"members[{index}].status 格式无效")
            if member["role"] == "maintainer" and member["status"] == "active":
                active_maintainers += 1
        if active_maintainers < 1:
            raise self._configuration_error("配置必须保留至少一名启用的 Maintainer")

        options = raw.get("knowledge_options", {})
        if not isinstance(options, dict):
            raise self._configuration_error("knowledge_options 必须是对象")
        categories = options.get("categories", {})
        if not isinstance(categories, dict) or set(categories) != LAYERS:
            raise self._configuration_error(
                "knowledge_options.categories 必须完整配置 layer0p/layer1/layer2/layer3"
            )
        for layer, values in categories.items():
            if not isinstance(values, list) or not values:
                raise self._configuration_error(f"categories.{layer} 必须是非空数组")
            if len(values) != len(set(values)) or any(
                not isinstance(value, str)
                or not SAFE_SEGMENT_PATTERN.fullmatch(value)
                or value == "archive"
                for value in values
            ):
                raise self._configuration_error(f"categories.{layer} 含有重复或不安全值")
        self.normalize_business_domains(options.get("business_domains", []))
        return raw

    def normalize_business_domains(self, domains: Any) -> List[Dict[str, str]]:
        if not isinstance(domains, list):
            raise self._configuration_error("business_domains 必须是数组")
        normalized: List[Dict[str, str]] = []
        seen = set()
        for index, value in enumerate(domains):
            if isinstance(value, str):
                domain = {"id": value, "name": value, "description": ""}
            elif isinstance(value, dict):
                if set(value) - {"id", "name", "description"}:
                    raise self._configuration_error(
                        f"business_domains[{index}] 包含未知字段"
                    )
                domain = {
                    "id": value.get("id"),
                    "name": value.get("name"),
                    "description": value.get("description", ""),
                }
            else:
                raise self._configuration_error(
                    f"business_domains[{index}] 必须是字符串或对象"
                )

            domain_id = domain["id"]
            name = domain["name"]
            description = domain["description"]
            if (
                not isinstance(domain_id, str)
                or not SAFE_SEGMENT_PATTERN.fullmatch(domain_id)
                or domain_id == "archive"
                or domain_id in seen
            ):
                raise self._configuration_error(
                    f"business_domains[{index}].id 重复或不安全"
                )
            if (
                not isinstance(name, str)
                or not name.strip()
                or len(name) > 80
                or any(ord(character) < 32 or ord(character) == 127 for character in name)
            ):
                raise self._configuration_error(
                    f"business_domains[{index}].name 格式无效"
                )
            if (
                not isinstance(description, str)
                or len(description) > 240
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in description
                )
            ):
                raise self._configuration_error(
                    f"business_domains[{index}].description 格式无效"
                )
            seen.add(domain_id)
            normalized.append(
                {
                    "id": domain_id,
                    "name": name.strip(),
                    "description": description.strip(),
                }
            )
        return normalized

    def knowledge_options(self) -> Dict[str, Any]:
        options = deepcopy(self.load_config()["knowledge_options"])
        options["business_domains"] = self.normalize_business_domains(
            options.get("business_domains", [])
        )
        return options

    def list_members(self) -> List[Dict[str, str]]:
        members = deepcopy(self.load_config()["members"])
        return sorted(members, key=lambda item: item["id"])

    def get_member(self, member_id: str, *, require_active: bool = True) -> Dict[str, str]:
        for member in self.load_config()["members"]:
            if member["id"] == member_id:
                if require_active and member["status"] != "active":
                    raise ApiError(403, "member_disabled", "当前成员已停用")
                return deepcopy(member)
        raise ApiError(401, "unknown_identity", "当前身份不在团队成员配置中")

    @staticmethod
    def require_role(member: Dict[str, str], *allowed: str) -> None:
        if member["role"] not in allowed:
            raise ApiError(403, "permission_denied", "当前角色无权执行该操作")

    @staticmethod
    def _ensure_active_maintainer(members: List[Dict[str, str]]) -> None:
        if not any(
            item["role"] == "maintainer" and item["status"] == "active"
            for item in members
        ):
            raise ApiError(
                409,
                "last_maintainer_protected",
                "不能降级或停用最后一名启用的 Maintainer",
            )

    def _write_config(self, config: Dict[str, Any]) -> None:
        rendered = yaml.safe_dump(
            config,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        governance.atomic_write(self.path, rendered)

    def write_config_and_audit(
        self,
        config: Dict[str, Any],
        *,
        actor_id: str,
        action: str,
        target_id: str,
        detail: str,
        session: str = "web:members",
    ) -> None:
        log_path = self.repo / "log.md"
        previous_config = self.path.read_text(encoding="utf-8")
        previous_log = log_path.read_text(encoding="utf-8") if log_path.exists() else None
        try:
            self._write_config(config)
            governance.append_log(
                self.repo,
                actor_id,
                action,
                target_id,
                detail,
                session,
            )
        except Exception:
            governance.atomic_write(self.path, previous_config)
            if previous_log is None:
                if log_path.exists():
                    log_path.unlink()
            else:
                governance.atomic_write(log_path, previous_log)
            raise

    def create_member(self, actor: Dict[str, str], request: MemberCreate) -> Dict[str, str]:
        with self.write_lock.acquire():
            current_actor = self.get_member(actor["id"])
            self.require_role(current_actor, "maintainer")
            config = self.load_config()
            if any(item["id"].casefold() == request.id.casefold() for item in config["members"]):
                raise ApiError(409, "member_exists", f"成员 ID 已存在：{request.id}")
            member = {
                "id": request.id,
                "display_name": request.display_name,
                "role": request.role,
                "status": "active",
            }
            config["members"].append(member)
            self._ensure_active_maintainer(config["members"])
            self.write_config_and_audit(
                config,
                actor_id=current_actor["id"],
                action="member-create",
                target_id=member["id"],
                detail=json.dumps({"after": member}, ensure_ascii=False, sort_keys=True),
            )
            return deepcopy(member)

    def patch_member(
        self,
        actor: Dict[str, str],
        member_id: str,
        request: MemberPatch,
    ) -> Dict[str, str]:
        if not MEMBER_ID_PATTERN.fullmatch(member_id):
            raise ApiError(404, "member_not_found", "成员不存在")
        with self.write_lock.acquire():
            current_actor = self.get_member(actor["id"])
            self.require_role(current_actor, "maintainer")
            config = self.load_config()
            target = next((item for item in config["members"] if item["id"] == member_id), None)
            if target is None:
                raise ApiError(404, "member_not_found", "成员不存在")
            before = deepcopy(target)
            updates = request.model_dump(exclude_none=True)
            target.update(updates)
            self._ensure_active_maintainer(config["members"])
            if target != before:
                self.write_config_and_audit(
                    config,
                    actor_id=current_actor["id"],
                    action="member-update",
                    target_id=member_id,
                    detail=json.dumps(
                        {"before": before, "after": target},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
            return deepcopy(target)
