from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from jsonschema import Draft202012Validator, FormatChecker

from .evidence import effective_events
from .models import EvidenceRecord, Finding, KnowledgeRecord
from .yaml_io import load_json


COMMON_SECTIONS = ("结论", "背景与问题", "适用条件", "不适用条件", "详细说明", "验证方式", "来源")
TYPE_SECTIONS = {
    "model": ("实体或概念定义", "属性", "关系", "不变量", "权威来源"),
    "decision": ("决策背景", "约束条件", "候选方案", "最终选择", "选择理由", "代价和后果", "重新决策条件"),
    "guideline": ("具体行为", "预期收益", "例外情况"),
    "pitfall": ("触发条件", "问题现象", "根本原因", "复现方式", "规避或修复方法", "修复验证"),
    "process": ("参与角色", "前置条件", "流程步骤", "状态转换", "异常分支", "权威确认人"),
}


def _schema_findings(record_path: Path, data: dict, schema: dict) -> List[Finding]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [Finding("error", str(record_path), f"Schema {'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}") for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path))]


def _expected_scope(path: Path) -> str:
    parts = path.parts
    if "archive" in parts:
        return "archive"
    mapping = {"team-conventions": "team", "tech-wiki": "tech", "biz-wiki": "biz"}
    for directory, scope in mapping.items():
        if directory in parts:
            return scope
    return ""


def validate(root: Path, records: Iterable[KnowledgeRecord], evidence: Dict[str, EvidenceRecord]) -> List[Finding]:
    records = list(records)
    findings: List[Finding] = []
    knowledge_schema = load_json(root / "schemas" / "knowledge.schema.json")
    evidence_schema = load_json(root / "schemas" / "evidence.schema.json")
    id_counts = Counter(record.id for record in records)
    known_ids = set(id_counts)
    for record in records:
        relative = record.path.relative_to(root)
        findings.extend(_schema_findings(relative, record.metadata, knowledge_schema))
        if id_counts[record.id] > 1:
            findings.append(Finding("error", str(relative), f"知识 ID 重复：{record.id}"))
        expected = _expected_scope(relative)
        if expected not in {"", "archive"} and record.metadata.get("scope") != expected:
            findings.append(Finding("error", str(relative), f"scope={record.metadata.get('scope')} 与目录要求的 {expected} 不一致"))
        if expected == "archive" and record.metadata.get("status") != "archived":
            findings.append(Finding("error", str(relative), "archive 目录中的知识必须为 archived"))
        headings = set(re.findall(r"^##\s+(.+?)\s*$", record.body, re.MULTILINE))
        for section in COMMON_SECTIONS + TYPE_SECTIONS.get(record.metadata.get("type"), ()):
            if section not in headings:
                findings.append(Finding("error", str(relative), f"缺少正文段落：## {section}"))
        for linked_id in list(record.metadata.get("supersedes") or []) + ([record.metadata.get("superseded_by")] if record.metadata.get("superseded_by") else []):
            if linked_id not in known_ids:
                findings.append(Finding("error", str(relative), f"引用的替代知识不存在：{linked_id}"))
    for knowledge_id, item in evidence.items():
        relative = item.path.relative_to(root)
        raw = {"schema_version": 1, "knowledge_id": item.knowledge_id, "events": item.events}
        findings.extend(_schema_findings(relative, raw, evidence_schema))
        if knowledge_id not in known_ids:
            findings.append(Finding("error", str(relative), f"Evidence 对应的知识不存在：{knowledge_id}"))
        event_ids = [event.get("event_id") for event in item.events]
        for event_id, count in Counter(event_ids).items():
            if count > 1:
                findings.append(Finding("error", str(relative), f"event_id 重复：{event_id}"))
    normalized_titles: Dict[str, List[str]] = {}
    for record in records:
        title = re.sub(r"\s+", "", str(record.metadata.get("title", "")).lower())
        normalized_titles.setdefault(title, []).append(record.id)
    for title, ids in normalized_titles.items():
        if title and len(ids) > 1:
            findings.append(Finding("warning", "knowledge-tree", f"疑似精确重复标题：{', '.join(sorted(ids))}"))
    return sorted(findings, key=lambda item: (item.severity != "error", item.path, item.message))
