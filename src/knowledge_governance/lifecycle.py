from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .evidence import effective_events


def parse_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def parse_date(value: str) -> dt.datetime:
    return dt.datetime.combine(dt.date.fromisoformat(str(value)[:10]), dt.time.min, tzinfo=dt.timezone.utc)


def duration_days(value: str) -> int:
    match = re.fullmatch(r"([1-9][0-9]*)d", str(value))
    if not match:
        raise ValueError(f"无效周期：{value}")
    return int(match.group(1))


def review_interval(metadata: Dict[str, Any], policy: Dict[str, Any]) -> str:
    override = metadata.get("review_policy_override") or {}
    if override.get("interval"):
        return override["interval"]
    domain = metadata.get("domain")
    risk = metadata.get("risk_level")
    scope = metadata.get("scope")
    return (policy.get("by_domain", {}).get(domain) or policy.get("by_risk", {}).get(risk) or policy.get("by_scope", {}).get(scope) or policy.get("default_interval", "180d"))


def derived_dates(metadata: Dict[str, Any], events: Iterable[Dict[str, Any]], review_policy: Dict[str, Any]) -> Dict[str, Optional[str]]:
    active = effective_events(events)
    successes = [parse_datetime(event["occurred_at"]) for event in active if event.get("event_type") == "validated_success"]
    reviews = [parse_datetime(event["occurred_at"]) for event in active if event.get("event_type") == "review_completed"]
    created = parse_date(metadata["created_at"])
    base = max([created] + successes + reviews)
    next_review = base + dt.timedelta(days=duration_days(review_interval(metadata, review_policy)))
    return {
        "last_validated_at": max(successes).isoformat() if successes else None,
        "last_reviewed_at": max(reviews).isoformat() if reviews else None,
        "next_review_at": next_review.date().isoformat(),
    }


def validation_counts(events: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    successes = [event for event in effective_events(events) if event.get("event_type") == "validated_success"]
    groups = {event.get("evidence_group_id") for event in successes if event.get("evidence_group_id")}
    projects = {event.get("project") for event in successes if event.get("project")}
    contributors = {event.get("operator") or event.get("contributor") for event in successes if event.get("operator") or event.get("contributor")}
    references = {event.get("reference") for event in successes if event.get("reference")}
    return {"successes": len(successes), "evidence_groups": len(groups), "projects": len(projects), "contributors": len(contributors), "references": len(references)}


def blockers(events: Iterable[Dict[str, Any]]) -> List[str]:
    types = {event.get("event_type") for event in effective_events(events)}
    result = []
    if "validated_failure" in types:
        result.append("存在未解决的 validated_failure")
    if "contradiction_found" in types:
        result.append("存在未解决的 contradiction_found")
    return result


def evaluate(metadata: Dict[str, Any], events: Iterable[Dict[str, Any]], review_policy: Dict[str, Any], maturity_policy: Dict[str, Any], today: dt.date) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    status = metadata["status"]
    maturity = metadata["maturity"]
    blocked = blockers(events)
    dates = derived_dates(metadata, events, review_policy)
    counts = validation_counts(events)
    if blocked and status not in {"disputed", "deprecated", "archived"}:
        proposals.append({"kind": "status", "from": status, "to": "disputed", "reasons": blocked})
        return proposals
    if status == "active" and dt.date.fromisoformat(dates["next_review_at"]) <= today:
        proposals.append({"kind": "status", "from": "active", "to": "review_due", "reasons": [f"next_review_at={dates['next_review_at']} 已到期"]})
    if blocked or status not in {"active", "review_due"}:
        return proposals
    if maturity == "draft" and counts["successes"] >= int(maturity_policy.get("verified", {}).get("minimum_successes", 1)):
        proposals.append({"kind": "maturity", "from": "draft", "to": "verified", "reasons": [f"有效成功验证 {counts['successes']} 次"]})
    proven = maturity_policy.get("proven", {})
    if maturity == "verified" and counts["successes"] >= int(proven.get("minimum_successes", 2)) and counts["evidence_groups"] >= int(proven.get("minimum_evidence_groups", 2)) and counts["projects"] >= int(proven.get("minimum_projects_or_confirmed_scenarios", 2)) and counts["contributors"] >= int(proven.get("minimum_contributors", 2)):
        proposals.append({"kind": "maturity", "from": "verified", "to": "proven", "reasons": [f"成功验证={counts['successes']}，证据组={counts['evidence_groups']}，项目={counts['projects']}，贡献者={counts['contributors']}", "需要 Owner 或 CODEOWNER 审批"]})
    return proposals
