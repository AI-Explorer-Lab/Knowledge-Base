from __future__ import annotations

import datetime as dt
import os
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from .lifecycle import blockers, derived_dates
from .models import EvidenceRecord, KnowledgeRecord
from .yaml_io import atomic_write


def _table(root: Path, catalog_path: Path, records: Iterable[KnowledgeRecord], evidence: Dict[str, EvidenceRecord], review_policy: dict) -> str:
    lines = ["| ID | 标题 | 类型 | 成熟度 | 状态 | 最近验证 | 下次复核 |", "|---|---|---|---|---|---|---|"]
    for record in sorted(records, key=lambda item: (item.metadata.get("scope", ""), item.id)):
        item = evidence.get(record.id)
        events = item.events if item else []
        dates = derived_dates(record.metadata, events, review_policy)
        effective_status = "disputed（安全保护）" if blockers(events) and record.metadata["status"] not in {"deprecated", "archived"} else record.metadata["status"]
        link = Path(os.path.relpath(record.path, start=catalog_path.parent)).as_posix()
        lines.append(f"| [{record.id}]({link}) | {record.metadata['title']} | {record.metadata['type']} | {record.metadata['maturity']} | {effective_status} | {dates['last_validated_at'] or '-'} | {dates['next_review_at']} |")
    return "\n".join(lines)


def build_catalogs(root: Path, records: List[KnowledgeRecord], evidence: Dict[str, EvidenceRecord], review_policy: dict) -> List[Path]:
    included = [record for record in records if record.metadata.get("status") != "archived"]
    statuses = Counter(record.metadata.get("status") for record in records)
    maturities = Counter(record.metadata.get("maturity") for record in records)
    written = [root / "knowledge-catalog.md"]
    summary = ["# 知识目录", "", "> 本文件由 `knowledge build-catalog` 生成，请勿手工编辑。", "", f"知识总数：{len(records)}", "", "## 健康摘要", "", f"- 成熟度：{', '.join(f'{key}={maturities[key]}' for key in sorted(maturities))}", f"- 状态：{', '.join(f'{key}={statuses[key]}' for key in sorted(statuses))}", "", "## 活跃知识", "", _table(root, written[0], included, evidence, review_policy), ""]
    atomic_write(written[0], "\n".join(summary))
    groups = [(root / "tech-wiki" / "catalog.md", [record for record in included if record.metadata.get("scope") == "tech"])]
    for domain_dir in sorted((root / "biz-wiki").glob("*")) if (root / "biz-wiki").exists() else []:
        if domain_dir.is_dir():
            groups.append((domain_dir / "catalog.md", [record for record in included if domain_dir in record.path.parents]))
    for path, group in groups:
        heading = path.parent.name
        atomic_write(path, f"# {heading} 知识目录\n\n> 自动生成，请勿手工编辑。\n\n{_table(root, path, group, evidence, review_policy)}\n")
        written.append(path)
    due = []
    today = dt.date.today()
    for record in records:
        item = evidence.get(record.id)
        dates = derived_dates(record.metadata, item.events if item else [], review_policy)
        if dt.date.fromisoformat(dates["next_review_at"]) <= today and record.metadata.get("status") not in {"deprecated", "archived"}:
            due.append(f"- {record.id} {record.metadata['title']}（{dates['next_review_at']}）")
    report = root / "reports" / "review-due.md"
    atomic_write(report, "# 待复核知识\n\n> 自动生成，请勿手工编辑。\n\n" + ("\n".join(due) if due else "当前没有待复核知识。") + "\n")
    written.append(report)
    return written
