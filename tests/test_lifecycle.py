import datetime as dt

from knowledge_governance.lifecycle import derived_dates, evaluate


METADATA = {
    "created_at": "2026-01-01",
    "scope": "tech",
    "domain": "messaging",
    "risk_level": "medium",
    "maturity": "verified",
    "status": "active",
}
REVIEW = {"default_interval": "180d", "by_scope": {"tech": "180d"}}
MATURITY = {
    "verified": {"minimum_successes": 1},
    "proven": {"minimum_successes": 2, "minimum_evidence_groups": 2, "minimum_projects_or_confirmed_scenarios": 2, "minimum_contributors": 2},
}


def success(event_id, project, group, contributor, occurred_at):
    return {"event_id": event_id, "event_type": "validated_success", "occurred_at": occurred_at, "project": project, "scenario_id": "duplicate-delivery", "evidence_group_id": group, "contributor": contributor, "validation_method": "test", "result_summary": "ok", "reference": f"{project}#1"}


def test_dates_are_derived_from_evidence_and_policy():
    events = [success("E1", "a", "g1", "user:a", "2026-06-01T00:00:00+00:00")]
    dates = derived_dates(METADATA, events, REVIEW)
    assert dates["last_validated_at"] == "2026-06-01T00:00:00+00:00"
    assert dates["next_review_at"] == "2026-11-28"


def test_two_independent_validations_propose_proven():
    events = [
        success("E1", "a", "g1", "user:a", "2026-05-01T00:00:00+00:00"),
        success("E2", "b", "g2", "user:b", "2026-06-01T00:00:00+00:00"),
    ]
    proposals = evaluate(METADATA, events, REVIEW, MATURITY, dt.date(2026, 7, 11))
    assert any(item["to"] == "proven" for item in proposals)


def test_failure_activates_disputed_safety_transition():
    events = [{"event_id": "F1", "event_type": "validated_failure", "occurred_at": "2026-07-01T00:00:00+00:00"}]
    proposals = evaluate(METADATA, events, REVIEW, MATURITY, dt.date(2026, 7, 11))
    assert proposals == [{"kind": "status", "from": "active", "to": "disputed", "reasons": ["存在未解决的 validated_failure"]}]
