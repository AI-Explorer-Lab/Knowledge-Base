import pytest

from knowledge_governance.errors import KnowledgeError
from knowledge_governance.evidence import append_event
from knowledge_governance.yaml_io import load_yaml


def test_append_event_is_idempotent_and_rejects_conflicting_payload(tmp_path):
    (tmp_path / "evidence").mkdir()
    event = {
        "event_id": "EVT-001",
        "event_type": "referenced",
        "occurred_at": "2026-07-11T10:00:00+00:00",
        "contributor": "user:alice",
    }
    assert append_event(tmp_path, "TK-001", event) is True
    assert append_event(tmp_path, "TK-001", event) is False
    assert len(load_yaml(tmp_path / "evidence" / "TK-001.yaml")["events"]) == 1
    with pytest.raises(KnowledgeError, match="内容不同"):
        append_event(tmp_path, "TK-001", {**event, "contributor": "user:bob"})
