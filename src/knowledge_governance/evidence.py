from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .errors import KnowledgeError
from .yaml_io import atomic_write, dump_yaml, load_yaml


def effective_events(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events = list(events)
    revoked = {event.get("revokes_event_id") for event in events if event.get("revokes_event_id")}
    superseded = {event.get("supersedes_event_id") for event in events if event.get("supersedes_event_id")}
    inactive = revoked | superseded
    return [event for event in events if event.get("event_id") not in inactive and event.get("event_type") not in {"event_correction", "event_revoked"}]


def append_event(root: Path, knowledge_id: str, event: Dict[str, Any]) -> bool:
    path = root / "evidence" / f"{knowledge_id}.yaml"
    data = load_yaml(path, {"schema_version": 1, "knowledge_id": knowledge_id, "events": []})
    if data.get("knowledge_id") != knowledge_id:
        raise KnowledgeError(f"{path}: knowledge_id 与文件名不一致")
    existing = {item.get("event_id"): item for item in data.get("events", [])}
    event_id = event["event_id"]
    if event_id in existing:
        if existing[event_id] == event:
            return False
        raise KnowledgeError(f"event_id {event_id} 已存在但内容不同")
    data.setdefault("events", []).append(event)
    data["events"].sort(key=lambda item: (str(item.get("occurred_at", "")), str(item.get("event_id", ""))))
    atomic_write(path, dump_yaml(data))
    log_line = f"- {event['occurred_at']} evidence {knowledge_id} {event['event_type']} {event_id}\n"
    with (root / "log.md").open("a", encoding="utf-8") as handle:
        handle.write(log_line)
    return True


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
