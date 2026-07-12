#!/usr/bin/env python3
"""File-based governance commands for the AI Team knowledge base.

The tool deliberately uses only Python's standard library. Knowledge remains in
Markdown files; a fenced JSON block at the top contains the metadata that must
be machine validated.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


KNOWLEDGE_TYPES = {"model", "decision", "guideline", "pitfall", "process"}
LAYERS = {"layer1", "layer2", "layer3"}
MATURITIES = {"draft", "verified", "proven"}
CONFLICT_STATES = {"none", "suspected", "confirmed", "resolved"}
VALIDATION_RESULTS = {"passed", "failed"}
ROLES = {"reader", "contributor", "maintainer", "system"}

PROVEN_DECAY_DAYS = 365
VERIFIED_DECAY_DAYS = 180
DRAFT_ARCHIVE_DAYS = 180

METADATA_PATTERN = re.compile(
    r"\A```knowledge-metadata[ \t]*\n(?P<json>.*?)\n```[ \t]*(?:\n|\Z)",
    re.DOTALL,
)
CATALOG_START = "<!-- knowledge-index:start -->"
CATALOG_END = "<!-- knowledge-index:end -->"
SUMMARY_START = "<!-- knowledge-summary:start -->"
SUMMARY_END = "<!-- knowledge-summary:end -->"
SPECIAL_MARKDOWN_FILES = {"catalog.md", "migration-log.md"}


class GovernanceError(Exception):
    """A user-facing governance failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("时间必须是非空字符串")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    result = datetime.fromisoformat(normalized)
    if result.tzinfo is None:
        raise ValueError("时间必须包含时区")
    return result.astimezone(timezone.utc)


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "knowledge-catalog.md").exists():
            return candidate
    raise GovernanceError("找不到知识库根目录（缺少 knowledge-catalog.md）")


def resolve_repo(value: Optional[str]) -> Path:
    return find_repo_root(Path(value) if value else Path.cwd())


def resolve_inside(repo: Path, value: str) -> Path:
    raw = Path(value)
    result = (raw if raw.is_absolute() else repo / raw).resolve()
    try:
        result.relative_to(repo.resolve())
    except ValueError as exc:
        raise GovernanceError(f"路径必须位于知识库内：{value}") from exc
    return result


def require_role(role: str, allowed: Sequence[str]) -> None:
    if role not in ROLES:
        raise GovernanceError(f"未知角色：{role}")
    if role not in allowed:
        raise GovernanceError(f"角色 {role} 无权执行该操作；允许角色：{', '.join(allowed)}")


def read_entry(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise GovernanceError(f"知识条目不存在：{path}") from exc
    match = METADATA_PATTERN.match(text)
    if not match:
        raise GovernanceError(f"缺少文件顶部的 knowledge-metadata 元数据块：{path}")
    try:
        metadata = json.loads(match.group("json"))
    except json.JSONDecodeError as exc:
        raise GovernanceError(f"元数据不是合法 JSON：{path}:{exc.lineno}:{exc.colno}") from exc
    if not isinstance(metadata, dict):
        raise GovernanceError(f"元数据必须是 JSON 对象：{path}")
    return metadata, text[match.end() :]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def write_entry(path: Path, metadata: Dict[str, Any], body: str) -> None:
    encoded = json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)
    normalized_body = body.lstrip("\n")
    atomic_write(path, f"```knowledge-metadata\n{encoded}\n```\n\n{normalized_body}")


def ensure_list(value: Any, field: str, errors: List[str]) -> List[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} 必须是数组")
        return []
    return value


def validate_record_fields(
    record: Any,
    required: Sequence[str],
    prefix: str,
    errors: List[str],
) -> Optional[Dict[str, Any]]:
    if not isinstance(record, dict):
        errors.append(f"{prefix} 必须是对象")
        return None
    for field in required:
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{prefix}.{field} 必须是非空字符串")
    return record


def validate_metadata(metadata: Dict[str, Any], body: str) -> List[str]:
    errors: List[str] = []
    for field in ("id", "title", "type", "layer", "maturity", "created_at"):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            errors.append(f"{field} 必须是非空字符串")

    if metadata.get("type") not in KNOWLEDGE_TYPES:
        errors.append(f"type 必须是以下值之一：{', '.join(sorted(KNOWLEDGE_TYPES))}")
    if metadata.get("layer") not in LAYERS:
        errors.append(f"layer 必须是以下值之一：{', '.join(sorted(LAYERS))}")
    if metadata.get("maturity") not in MATURITIES:
        errors.append(f"maturity 必须是以下值之一：{', '.join(sorted(MATURITIES))}")
    if metadata.get("conflict_status") not in CONFLICT_STATES:
        errors.append(f"conflict_status 必须是以下值之一：{', '.join(sorted(CONFLICT_STATES))}")

    try:
        parse_time(metadata.get("created_at", ""))
    except (TypeError, ValueError) as exc:
        errors.append(f"created_at 非法：{exc}")

    tags = ensure_list(metadata.get("tags"), "tags", errors)
    if any(not isinstance(item, str) or not item.strip() for item in tags):
        errors.append("tags 中的每一项必须是非空字符串")
    sources = ensure_list(metadata.get("source_references"), "source_references", errors)
    if not sources:
        errors.append("source_references 至少包含一个来源")
    if any(not isinstance(item, str) or not item.strip() for item in sources):
        errors.append("source_references 中的每一项必须是非空字符串")

    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence 必须是对象")
        evidence = {}
    contributors = ensure_list(evidence.get("contributors"), "evidence.contributors", errors)
    if any(not isinstance(item, str) or not item.strip() for item in contributors):
        errors.append("evidence.contributors 中的每一项必须是非空字符串")

    references = ensure_list(evidence.get("references"), "evidence.references", errors)
    for index, record in enumerate(references):
        validated = validate_record_fields(
            record,
            ("project_id", "workflow_id", "contributor", "referenced_at", "used_in"),
            f"evidence.references[{index}]",
            errors,
        )
        if validated:
            try:
                parse_time(validated.get("referenced_at", ""))
            except (TypeError, ValueError) as exc:
                errors.append(f"evidence.references[{index}].referenced_at 非法：{exc}")

    validations = ensure_list(evidence.get("validations"), "evidence.validations", errors)
    for index, record in enumerate(validations):
        validated = validate_record_fields(
            record,
            ("project_id", "workflow_id", "contributor", "validated_at", "result", "source"),
            f"evidence.validations[{index}]",
            errors,
        )
        if validated:
            if validated.get("result") not in VALIDATION_RESULTS:
                errors.append(
                    f"evidence.validations[{index}].result 必须是 passed 或 failed"
                )
            try:
                parse_time(validated.get("validated_at", ""))
            except (TypeError, ValueError) as exc:
                errors.append(f"evidence.validations[{index}].validated_at 非法：{exc}")

    promotion = metadata.get("promotion")
    if not isinstance(promotion, dict):
        errors.append("promotion 必须是对象")
        promotion = {}
    if not isinstance(promotion.get("candidate"), bool):
        errors.append("promotion.candidate 必须是布尔值")
    target_layer = promotion.get("target_layer")
    if target_layer not in (None, "layer1", "layer2"):
        errors.append("promotion.target_layer 必须为空、layer1 或 layer2")
    target_path = promotion.get("target_path")
    if target_path is not None and (not isinstance(target_path, str) or not target_path.strip()):
        errors.append("promotion.target_path 必须为空或非空字符串")
    history = ensure_list(promotion.get("previous_layers"), "promotion.previous_layers", errors)
    if any(not isinstance(item, dict) for item in history):
        errors.append("promotion.previous_layers 中的每一项必须是对象")
    if promotion.get("candidate") and (not target_layer or not target_path):
        errors.append("提升候选必须填写 promotion.target_layer 和 promotion.target_path")

    if not body.strip():
        errors.append("知识正文不能为空")
    return errors


def layer_context(repo: Path, path: Path) -> Tuple[str, Path, bool, Path]:
    relative = path.resolve().relative_to(repo.resolve())
    parts = relative.parts
    if not parts:
        raise GovernanceError(f"无法识别知识层级：{path}")

    if parts[0] == "tech-wiki":
        root = repo / "tech-wiki"
        layer = "layer1"
        remainder = Path(*parts[1:])
    elif len(parts) >= 2 and parts[0] == "biz-wiki":
        root = repo / "biz-wiki" / parts[1]
        layer = "layer2"
        remainder = Path(*parts[2:])
    elif len(parts) >= 2 and parts[:2] == ("docs", "knowledge"):
        root = repo / "docs" / "knowledge"
        layer = "layer3"
        remainder = Path(*parts[2:])
    else:
        raise GovernanceError(f"知识条目必须位于 Layer 1、Layer 2 或 Layer 3：{relative}")

    remainder_parts = remainder.parts
    archived = bool(remainder_parts and remainder_parts[0] == "archive")
    active_relative = Path(*remainder_parts[1:]) if archived else remainder
    if not active_relative.parts:
        raise GovernanceError(f"知识条目路径不能直接指向层级根目录：{relative}")
    return layer, root, archived, active_relative


def is_special_file(path: Path) -> bool:
    return path.name in SPECIAL_MARKDOWN_FILES or path.name.startswith(".")


def knowledge_roots(repo: Path) -> List[Path]:
    roots = [repo / "tech-wiki", repo / "docs" / "knowledge"]
    biz_root = repo / "biz-wiki"
    if biz_root.exists():
        roots.extend(path for path in biz_root.iterdir() if path.is_dir())
    return roots


def iter_candidate_files(repo: Path) -> Iterable[Path]:
    seen: set = set()
    for root in knowledge_roots(repo):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            resolved = path.resolve()
            if resolved in seen or is_special_file(path):
                continue
            seen.add(resolved)
            yield path


def is_entry_file(path: Path) -> bool:
    try:
        first = path.read_text(encoding="utf-8")[:64]
    except OSError:
        return False
    return first.startswith("```knowledge-metadata")


def active_entries(repo: Path) -> List[Tuple[Path, Dict[str, Any], str]]:
    entries: List[Tuple[Path, Dict[str, Any], str]] = []
    for path in iter_candidate_files(repo):
        if not is_entry_file(path):
            continue
        _, _, archived, _ = layer_context(repo, path)
        if archived:
            continue
        metadata, body = read_entry(path)
        entries.append((path, metadata, body))
    return entries


def passed_validations(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence = metadata.get("evidence", {})
    validations = evidence.get("validations", []) if isinstance(evidence, dict) else []
    return [item for item in validations if isinstance(item, dict) and item.get("result") == "passed"]


def has_successful_validation(metadata: Dict[str, Any]) -> bool:
    return bool(passed_validations(metadata))


def has_effective_validation(
    metadata: Dict[str, Any],
    as_of: datetime,
    max_age_days: int = VERIFIED_DECAY_DAYS,
) -> bool:
    for item in passed_validations(metadata):
        try:
            validated_at = parse_time(item.get("validated_at", ""))
        except (TypeError, ValueError):
            continue
        if (as_of - validated_at).days < max_age_days:
            return True
    return False


def eligible_for_proven(metadata: Dict[str, Any]) -> bool:
    validations = passed_validations(metadata)
    projects = {item.get("project_id") for item in validations if item.get("project_id")}
    contributors = {item.get("contributor") for item in validations if item.get("contributor")}
    return len(projects) >= 2 and len(contributors) >= 2


def conflict_blocks_upgrade(metadata: Dict[str, Any]) -> bool:
    return metadata.get("conflict_status") in {"suspected", "confirmed"}


def last_reference_time(metadata: Dict[str, Any]) -> datetime:
    candidates: List[datetime] = []
    evidence = metadata.get("evidence", {})
    if isinstance(evidence, dict):
        for item in evidence.get("references", []):
            if isinstance(item, dict):
                try:
                    candidates.append(parse_time(item.get("referenced_at", "")))
                except (TypeError, ValueError):
                    continue
    if candidates:
        return max(candidates)
    return parse_time(metadata["created_at"])


def touch_contributor(metadata: Dict[str, Any], actor: str) -> None:
    evidence = metadata.setdefault("evidence", {})
    contributors = evidence.setdefault("contributors", [])
    if actor not in contributors:
        contributors.append(actor)


def append_log(
    repo: Path,
    actor: str,
    action: str,
    knowledge_id: str,
    detail: str,
    session: str,
) -> None:
    path = repo / "log.md"
    current = path.read_text(encoding="utf-8") if path.exists() else "# 知识贡献日志\n"
    if not current.endswith("\n"):
        current += "\n"
    line = f"- {utc_now()} | `{actor}` | `{action}` | `{knowledge_id}` | {detail} | `{session}`\n"
    atomic_write(path, current + line)


def replace_managed_section(text: str, start: str, end: str, content: str) -> str:
    block = f"{start}\n{content.rstrip()}\n{end}"
    if start in text and end in text:
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        return f"{before}{block}{after}"
    separator = "\n" if text.endswith("\n") else "\n\n"
    return f"{text}{separator}{block}\n"


def catalog_rows(entries: Iterable[Tuple[Path, Dict[str, Any], str]], repo: Path) -> str:
    rows: List[str] = []
    for path, metadata, _ in sorted(entries, key=lambda item: str(item[0])):
        tags = ", ".join(metadata.get("tags", [])) or "-"
        relative = path.relative_to(repo).as_posix()
        rows.append(
            f"| `{metadata['id']}` | {metadata['title']} | `{metadata['type']}` | "
            f"`{metadata['maturity']}` | {tags} | `{relative}` |"
        )
    header = "| ID | 标题 | 类型 | 成熟度 | 标签 | 路径 |\n|---|---|---|---|---|---|"
    if not rows:
        return "## 活跃知识\n\n_当前没有活跃知识条目。_"
    return f"## 活跃知识\n\n{header}\n" + "\n".join(rows)


def expected_catalogs(repo: Path) -> Dict[Path, str]:
    grouped: Dict[Path, List[Tuple[Path, Dict[str, Any], str]]] = {}
    for root in knowledge_roots(repo):
        if root.exists():
            grouped[root] = []
    for entry in active_entries(repo):
        _, root, _, _ = layer_context(repo, entry[0])
        grouped.setdefault(root, []).append(entry)
    return {root / "catalog.md": catalog_rows(entries, repo) for root, entries in grouped.items()}


def summary_section(repo: Path) -> str:
    active_counts = {layer: 0 for layer in sorted(LAYERS)}
    archived_counts = {layer: 0 for layer in sorted(LAYERS)}
    for path in iter_candidate_files(repo):
        if not is_entry_file(path):
            continue
        layer, _, archived, _ = layer_context(repo, path)
        (archived_counts if archived else active_counts)[layer] += 1
    return (
        "## 治理状态摘要\n\n"
        "| 层级 | 活跃条目 | 归档条目 |\n|---|---:|---:|\n"
        f"| Layer 1 | {active_counts['layer1']} | {archived_counts['layer1']} |\n"
        f"| Layer 2 | {active_counts['layer2']} | {archived_counts['layer2']} |\n"
        f"| Layer 3 | {active_counts['layer3']} | {archived_counts['layer3']} |"
    )


def reindex(repo: Path) -> None:
    for path, section in expected_catalogs(repo).items():
        if path.exists():
            current = path.read_text(encoding="utf-8")
        else:
            current = "# 知识分类清单\n"
        atomic_write(path, replace_managed_section(current, CATALOG_START, CATALOG_END, section))

    root_catalog = repo / "knowledge-catalog.md"
    current = root_catalog.read_text(encoding="utf-8")
    atomic_write(
        root_catalog,
        replace_managed_section(current, SUMMARY_START, SUMMARY_END, summary_section(repo)),
    )


def migration_log(
    source_root: Path,
    knowledge_id: str,
    source: Path,
    target: Path,
    actor: str,
) -> None:
    path = source_root / "migration-log.md"
    current = path.read_text(encoding="utf-8") if path.exists() else "# 知识迁移记录\n"
    if not current.endswith("\n"):
        current += "\n"
    line = (
        f"- {utc_now()} | `{knowledge_id}` | `{source.as_posix()}` → "
        f"`{target.as_posix()}` | `{actor}`\n"
    )
    atomic_write(path, current + line)


def archive_target(repo: Path, path: Path) -> Path:
    _, root, archived, active_relative = layer_context(repo, path)
    if archived:
        raise GovernanceError("该知识已经归档")
    return root / "archive" / active_relative


def move_entry(source: Path, target: Path) -> None:
    if target.exists():
        raise GovernanceError(f"目标路径已存在：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)


def archive_entry(
    repo: Path,
    path: Path,
    actor: str,
    reason: str,
    session: str,
) -> Path:
    metadata, _ = read_entry(path)
    if metadata.get("maturity") != "draft":
        raise GovernanceError("只有 draft 知识可以归档")
    target = archive_target(repo, path)
    relative_source = path.relative_to(repo)
    relative_target = target.relative_to(repo)
    move_entry(path, target)
    append_log(
        repo,
        actor,
        "archive",
        metadata["id"],
        f"{relative_source.as_posix()} → {relative_target.as_posix()}；原因：{reason}",
        session,
    )
    return target


def cmd_create(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("contributor", "maintainer"))
    path = resolve_inside(repo, args.path)
    if path.exists():
        raise GovernanceError(f"目标文件已存在：{path}")
    actual_layer, _, archived, _ = layer_context(repo, path)
    if archived:
        raise GovernanceError("不能直接在 archive/ 中创建知识")
    if actual_layer != args.layer:
        raise GovernanceError(f"路径属于 {actual_layer}，与 --layer {args.layer} 不一致")
    for existing in iter_candidate_files(repo):
        if is_entry_file(existing) and read_entry(existing)[0].get("id") == args.id:
            raise GovernanceError(f"知识 ID 已存在：{args.id}")

    metadata: Dict[str, Any] = {
        "id": args.id,
        "title": args.title,
        "type": args.type,
        "layer": args.layer,
        "maturity": "draft",
        "created_at": utc_now(),
        "tags": args.tag or [],
        "source_references": args.source,
        "evidence": {
            "contributors": [args.actor],
            "references": [],
            "validations": [],
        },
        "promotion": {
            "candidate": False,
            "target_layer": None,
            "target_path": None,
            "previous_layers": [],
        },
        "conflict_status": "none",
    }
    body = f"# {args.title}\n\n{args.content.strip()}\n"
    errors = validate_metadata(metadata, body)
    if errors:
        raise GovernanceError("无法创建非法条目：\n- " + "\n- ".join(errors))
    write_entry(path, metadata, body)
    reindex(repo)
    append_log(repo, args.actor, "create", args.id, path.relative_to(repo).as_posix(), args.session)
    print(f"已创建：{path.relative_to(repo)}")


def cmd_reference(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("contributor", "maintainer"))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    _, _, archived, _ = layer_context(repo, path)
    if archived:
        raise GovernanceError("归档知识必须恢复后才能引用")
    record = {
        "project_id": args.project,
        "workflow_id": args.workflow,
        "contributor": args.actor,
        "referenced_at": args.at or utc_now(),
        "used_in": args.used_in,
    }
    parse_time(record["referenced_at"])
    metadata["evidence"]["references"].append(record)
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    append_log(repo, args.actor, "reference", metadata["id"], args.used_in, args.session)
    print(f"已记录引用：{metadata['id']}")


def cmd_validate(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("contributor", "maintainer"))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    _, _, archived, _ = layer_context(repo, path)
    if archived:
        raise GovernanceError("归档知识必须恢复后才能验证")
    record = {
        "project_id": args.project,
        "workflow_id": args.workflow,
        "contributor": args.actor,
        "validated_at": args.at or utc_now(),
        "result": args.result,
        "source": args.source,
    }
    parse_time(record["validated_at"])
    metadata["evidence"]["validations"].append(record)
    touch_contributor(metadata, args.actor)
    before = metadata["maturity"]
    if (
        args.result == "passed"
        and before == "draft"
        and not conflict_blocks_upgrade(metadata)
    ):
        metadata["maturity"] = "verified"
    write_entry(path, metadata, body)
    reindex(repo)
    detail = f"{args.result}；成熟度 {before} → {metadata['maturity']}"
    append_log(repo, args.actor, "validate", metadata["id"], detail, args.session)
    print(f"已记录验证：{metadata['id']}（{detail}）")


def cmd_approve_proven(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    if metadata.get("maturity") != "verified":
        raise GovernanceError("只有 verified 知识可以提升为 proven")
    if conflict_blocks_upgrade(metadata):
        raise GovernanceError("存在未解决冲突，成熟度提升已冻结")
    if not eligible_for_proven(metadata):
        raise GovernanceError("proven 需要至少两个不同项目、两个不同贡献者的成功验证")
    if (datetime.now(timezone.utc) - last_reference_time(metadata)).days >= VERIFIED_DECAY_DAYS:
        raise GovernanceError("该知识已达到 verified 衰减条件，请先执行 Lint 和重新验证")
    metadata["maturity"] = "proven"
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    reindex(repo)
    append_log(repo, args.actor, "approve-proven", metadata["id"], "verified → proven", args.session)
    print(f"已批准 proven：{metadata['id']}")


def destination_for_promotion(repo: Path, target_layer: str, target_path: str, filename: str) -> Path:
    relative = Path(target_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise GovernanceError("提升目标必须是安全的相对目录")
    if target_layer == "layer1":
        base = repo / "tech-wiki"
    elif target_layer == "layer2":
        if len(relative.parts) < 1:
            raise GovernanceError("Layer 2 目标必须以业务 domain 开头")
        base = repo / "biz-wiki"
    else:
        raise GovernanceError("提升目标只能是 layer1 或 layer2")
    return base / relative / filename


def cmd_propose_promotion(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("contributor", "maintainer"))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    actual_layer, _, archived, _ = layer_context(repo, path)
    if archived or actual_layer != "layer3":
        raise GovernanceError("只有活跃的 Layer 3 知识可以发起提升")
    if conflict_blocks_upgrade(metadata):
        raise GovernanceError("存在未解决冲突，层级提升已冻结")
    if not has_successful_validation(metadata):
        raise GovernanceError("提升候选至少需要一次成功验证")
    target = destination_for_promotion(repo, args.target_layer, args.destination, path.name)
    metadata["promotion"]["candidate"] = True
    metadata["promotion"]["target_layer"] = args.target_layer
    metadata["promotion"]["target_path"] = target.relative_to(repo).as_posix()
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    append_log(
        repo,
        args.actor,
        "propose-promotion",
        metadata["id"],
        f"{actual_layer} → {args.target_layer}；目标：{target.relative_to(repo)}",
        args.session,
    )
    print(f"已发起层级提升：{metadata['id']} → {args.target_layer}")


def cmd_approve_promotion(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    actual_layer, source_root, archived, _ = layer_context(repo, path)
    promotion = metadata.get("promotion", {})
    if archived or actual_layer != "layer3" or not promotion.get("candidate"):
        raise GovernanceError("该条目不是有效的 Layer 3 提升候选")
    if conflict_blocks_upgrade(metadata):
        raise GovernanceError("存在未解决冲突，层级提升已冻结")
    if not has_successful_validation(metadata):
        raise GovernanceError("提升候选至少需要一次成功验证")
    target = resolve_inside(repo, promotion["target_path"])
    target_layer, _, target_archived, _ = layer_context(repo, target)
    if target_archived or target_layer != promotion["target_layer"]:
        raise GovernanceError("提升目标路径与目标层级不一致")

    source_relative = path.relative_to(repo)
    target_relative = target.relative_to(repo)
    promotion["previous_layers"].append(
        {
            "from": actual_layer,
            "to": target_layer,
            "from_path": source_relative.as_posix(),
            "to_path": target_relative.as_posix(),
            "actor": args.actor,
            "changed_at": utc_now(),
        }
    )
    promotion["candidate"] = False
    promotion["target_layer"] = None
    promotion["target_path"] = None
    metadata["layer"] = target_layer
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    move_entry(path, target)
    migration_log(source_root, metadata["id"], source_relative, target_relative, args.actor)
    reindex(repo)
    append_log(
        repo,
        args.actor,
        "approve-promotion",
        metadata["id"],
        f"{source_relative.as_posix()} → {target_relative.as_posix()}",
        args.session,
    )
    print(f"已批准层级提升：{target_relative}")


def cmd_rollback_layer(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    actual_layer, source_root, archived, _ = layer_context(repo, path)
    if archived or actual_layer not in {"layer1", "layer2"}:
        raise GovernanceError("只有活跃的 Layer 1 或 Layer 2 知识可以退回 Layer 3")
    relative_destination = Path(args.destination)
    if relative_destination.is_absolute() or ".." in relative_destination.parts:
        raise GovernanceError("退回目标必须是 docs/knowledge/ 下的安全相对目录")
    target = repo / "docs" / "knowledge" / relative_destination / path.name
    source_relative = path.relative_to(repo)
    target_relative = target.relative_to(repo)
    metadata["promotion"]["previous_layers"].append(
        {
            "from": actual_layer,
            "to": "layer3",
            "from_path": source_relative.as_posix(),
            "to_path": target_relative.as_posix(),
            "actor": args.actor,
            "changed_at": utc_now(),
            "reason": args.reason,
        }
    )
    metadata["promotion"]["candidate"] = False
    metadata["promotion"]["target_layer"] = None
    metadata["promotion"]["target_path"] = None
    metadata["layer"] = "layer3"
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    move_entry(path, target)
    migration_log(source_root, metadata["id"], source_relative, target_relative, args.actor)
    reindex(repo)
    append_log(
        repo,
        args.actor,
        "rollback-layer",
        metadata["id"],
        f"{source_relative.as_posix()} → {target_relative.as_posix()}；原因：{args.reason}",
        args.session,
    )
    print(f"已退回 Layer 3：{target_relative}")


def cmd_archive(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    target = archive_entry(
        repo,
        resolve_inside(repo, args.path),
        args.actor,
        args.reason,
        args.session,
    )
    reindex(repo)
    print(f"已归档：{target.relative_to(repo)}")


def cmd_restore(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    _, root, archived, active_relative = layer_context(repo, path)
    if not archived:
        raise GovernanceError("该知识不在 archive/ 中")
    target = root / active_relative
    before = metadata.get("maturity")
    metadata["maturity"] = "draft"
    metadata["promotion"]["candidate"] = False
    metadata["promotion"]["target_layer"] = None
    metadata["promotion"]["target_path"] = None
    touch_contributor(metadata, args.actor)
    metadata["evidence"]["references"].append(
        {
            "project_id": "knowledge-base",
            "workflow_id": args.session,
            "contributor": args.actor,
            "referenced_at": utc_now(),
            "used_in": f"恢复归档知识：{args.reason}",
        }
    )
    write_entry(path, metadata, body)
    move_entry(path, target)
    reindex(repo)
    append_log(
        repo,
        args.actor,
        "restore",
        metadata["id"],
        f"{path.relative_to(repo)} → {target.relative_to(repo)}；{before} → draft；原因：{args.reason}",
        args.session,
    )
    print(f"已恢复为 draft：{target.relative_to(repo)}")


def conflict_record_path(repo: Path, knowledge_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return repo / "contributions" / "conflicts" / f"{knowledge_id}-{timestamp}.md"


def cmd_mark_conflict(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("contributor", "maintainer"))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    if metadata.get("conflict_status") in {"suspected", "confirmed"}:
        raise GovernanceError("该知识已经存在未解决冲突")
    metadata["conflict_status"] = "suspected"
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    record_path = conflict_record_path(repo, metadata["id"])
    record = {
        "knowledge_id": metadata["id"],
        "knowledge_path": path.relative_to(repo).as_posix(),
        "status": "suspected",
        "reported_by": args.actor,
        "reported_at": utc_now(),
        "reason": args.reason,
    }
    encoded = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True)
    atomic_write(record_path, f"# 知识冲突：{metadata['id']}\n\n```json\n{encoded}\n```\n")
    append_log(repo, args.actor, "mark-conflict", metadata["id"], args.reason, args.session)
    print(f"已冻结提升并创建冲突记录：{record_path.relative_to(repo)}")


def latest_conflict_record(repo: Path, knowledge_id: str) -> Optional[Path]:
    directory = repo / "contributions" / "conflicts"
    matches = sorted(directory.glob(f"{knowledge_id}-*.md")) if directory.exists() else []
    return matches[-1] if matches else None


def cmd_resolve_conflict(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer",))
    path = resolve_inside(repo, args.path)
    metadata, body = read_entry(path)
    if metadata.get("conflict_status") not in {"suspected", "confirmed"}:
        raise GovernanceError("该知识没有未解决冲突")
    metadata["conflict_status"] = "resolved"
    touch_contributor(metadata, args.actor)
    write_entry(path, metadata, body)
    record_path = latest_conflict_record(repo, metadata["id"])
    if record_path:
        current = record_path.read_text(encoding="utf-8")
        if not current.endswith("\n"):
            current += "\n"
        current += (
            f"## 裁决结果\n\n- 裁决人：`{args.actor}`\n- 时间：`{utc_now()}`\n"
            f"- 结论：{args.resolution}\n"
        )
        atomic_write(record_path, current)
    append_log(repo, args.actor, "resolve-conflict", metadata["id"], args.resolution, args.session)
    print(f"已解决冲突：{metadata['id']}")


def catalog_issues(repo: Path) -> List[str]:
    issues: List[str] = []
    for path, expected in expected_catalogs(repo).items():
        if not path.exists():
            issues.append(f"INDEX_MISSING {path.relative_to(repo)}")
            continue
        current = path.read_text(encoding="utf-8")
        rendered = replace_managed_section(current, CATALOG_START, CATALOG_END, expected)
        if current != rendered:
            issues.append(f"INDEX_STALE {path.relative_to(repo)}")
    root = repo / "knowledge-catalog.md"
    current = root.read_text(encoding="utf-8")
    rendered = replace_managed_section(current, SUMMARY_START, SUMMARY_END, summary_section(repo))
    if current != rendered:
        issues.append("INDEX_STALE knowledge-catalog.md")
    return issues


def lint_entries(repo: Path, as_of: datetime) -> Tuple[List[str], List[Tuple[Path, str]]]:
    issues: List[str] = []
    actions: List[Tuple[Path, str]] = []
    ids: Dict[str, Path] = {}

    for path in iter_candidate_files(repo):
        relative = path.relative_to(repo)
        if not is_entry_file(path):
            issues.append(f"METADATA_MISSING {relative}")
            continue
        try:
            metadata, body = read_entry(path)
            path_layer, _, archived, _ = layer_context(repo, path)
        except GovernanceError as exc:
            issues.append(f"INVALID {relative}: {exc}")
            continue

        errors = validate_metadata(metadata, body)
        for error in errors:
            issues.append(f"INVALID {relative}: {error}")
        if errors:
            continue
        if metadata["layer"] != path_layer:
            issues.append(
                f"LAYER_MISMATCH {relative}: metadata={metadata['layer']} path={path_layer}"
            )
        if archived and metadata["maturity"] != "draft":
            issues.append(f"ARCHIVE_MATURITY {relative}: 归档知识必须是 draft")

        knowledge_id = metadata["id"]
        if knowledge_id in ids:
            issues.append(
                f"DUPLICATE_ID {knowledge_id}: {ids[knowledge_id].relative_to(repo)} 与 {relative}"
            )
        else:
            ids[knowledge_id] = path

        if archived:
            continue
        last_reference = last_reference_time(metadata)
        age_days = (as_of - last_reference).days
        maturity = metadata["maturity"]
        if (
            maturity == "verified"
            and age_days < VERIFIED_DECAY_DAYS
            and eligible_for_proven(metadata)
        ):
            issues.append(f"PROVEN_REVIEW {relative}: 已满足 proven 条件，等待 Maintainer 审批")
        if maturity == "proven" and age_days >= PROVEN_DECAY_DAYS:
            issues.append(f"DECAY {relative}: proven 已 {age_days} 天未引用，应降为 verified")
            actions.append((path, "verified"))
        elif maturity == "verified" and age_days >= VERIFIED_DECAY_DAYS:
            issues.append(f"DECAY {relative}: verified 已 {age_days} 天未引用，应降为 draft")
            actions.append((path, "draft"))
        elif (
            maturity == "draft"
            and age_days >= DRAFT_ARCHIVE_DAYS
            and not has_effective_validation(metadata, as_of)
        ):
            issues.append(f"ARCHIVE_DUE {relative}: draft 已 {age_days} 天未引用且无有效成功验证")
            actions.append((path, "archive"))
    return issues, actions


def cmd_lint(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    if args.fix:
        require_role(args.role, ("maintainer", "system"))
    as_of = parse_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
    issues, actions = lint_entries(repo, as_of)
    issues.extend(catalog_issues(repo))

    if args.fix:
        for path, action in actions:
            if not path.exists():
                continue
            metadata, body = read_entry(path)
            if action in {"verified", "draft"}:
                before = metadata["maturity"]
                metadata["maturity"] = action
                write_entry(path, metadata, body)
                append_log(
                    repo,
                    args.actor,
                    "auto-decay",
                    metadata["id"],
                    f"{before} → {action}",
                    args.session,
                )
            elif action == "archive":
                archive_entry(repo, path, args.actor, "Lint：长期未引用且无有效成功验证", args.session)
        reindex(repo)

    if issues:
        for issue in issues:
            print(issue)
        if args.fix:
            print(f"已执行可自动修复项；本次发现 {len(issues)} 个问题或治理动作")
        else:
            raise GovernanceError(f"Lint 发现 {len(issues)} 个问题")
    else:
        print("Lint 通过：未发现问题")


def cmd_reindex(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    require_role(args.role, ("maintainer", "system"))
    reindex(repo)
    print("已更新全景目录和各层活跃索引")


def add_actor_options(parser: argparse.ArgumentParser, roles: Sequence[str]) -> None:
    parser.add_argument("--actor", required=True, help="操作者稳定 ID")
    parser.add_argument("--role", required=True, choices=roles)
    parser.add_argument("--session", default="manual", help="会话或工作流标识")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Team 知识库治理工具")
    parser.add_argument("--repo", help="知识库根目录；默认从当前目录向上查找")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="创建 draft 知识条目")
    create.add_argument("--path", required=True)
    create.add_argument("--id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--type", required=True, choices=sorted(KNOWLEDGE_TYPES))
    create.add_argument("--layer", required=True, choices=sorted(LAYERS))
    create.add_argument("--source", required=True, action="append")
    create.add_argument("--tag", action="append")
    create.add_argument("--content", required=True)
    add_actor_options(create, ("contributor", "maintainer"))
    create.set_defaults(func=cmd_create)

    reference = subparsers.add_parser("reference", help="记录一次知识引用")
    reference.add_argument("path")
    reference.add_argument("--project", required=True)
    reference.add_argument("--workflow", required=True)
    reference.add_argument("--used-in", required=True)
    reference.add_argument("--at", help="ISO 8601 引用时间；默认当前时间")
    add_actor_options(reference, ("contributor", "maintainer"))
    reference.set_defaults(func=cmd_reference)

    validate = subparsers.add_parser("validate", help="记录验证并自动执行 draft → verified")
    validate.add_argument("path")
    validate.add_argument("--project", required=True)
    validate.add_argument("--workflow", required=True)
    validate.add_argument("--result", required=True, choices=sorted(VALIDATION_RESULTS))
    validate.add_argument("--source", required=True)
    validate.add_argument("--at", help="ISO 8601 验证时间；默认当前时间")
    add_actor_options(validate, ("contributor", "maintainer"))
    validate.set_defaults(func=cmd_validate)

    proven = subparsers.add_parser("approve-proven", help="Maintainer 审批 verified → proven")
    proven.add_argument("path")
    add_actor_options(proven, ("maintainer",))
    proven.set_defaults(func=cmd_approve_proven)

    propose = subparsers.add_parser("propose-promotion", help="发起 Layer 3 层级提升")
    propose.add_argument("path")
    propose.add_argument("--target-layer", required=True, choices=("layer1", "layer2"))
    propose.add_argument(
        "--destination",
        required=True,
        help="目标层内的相对目录；Layer 2 必须以 domain 开头",
    )
    add_actor_options(propose, ("contributor", "maintainer"))
    propose.set_defaults(func=cmd_propose_promotion)

    approve = subparsers.add_parser("approve-promotion", help="Maintainer 审批并迁移提升候选")
    approve.add_argument("path")
    add_actor_options(approve, ("maintainer",))
    approve.set_defaults(func=cmd_approve_promotion)

    rollback = subparsers.add_parser("rollback-layer", help="将 Layer 1/2 条目退回 Layer 3")
    rollback.add_argument("path")
    rollback.add_argument("--destination", required=True, help="docs/knowledge/ 下的相对目录")
    rollback.add_argument("--reason", required=True)
    add_actor_options(rollback, ("maintainer",))
    rollback.set_defaults(func=cmd_rollback_layer)

    archive = subparsers.add_parser("archive", help="归档 draft 知识")
    archive.add_argument("path")
    archive.add_argument("--reason", required=True)
    add_actor_options(archive, ("maintainer",))
    archive.set_defaults(func=cmd_archive)

    restore = subparsers.add_parser("restore", help="从 archive/ 恢复为 draft")
    restore.add_argument("path")
    restore.add_argument("--reason", required=True)
    add_actor_options(restore, ("maintainer",))
    restore.set_defaults(func=cmd_restore)

    mark = subparsers.add_parser("mark-conflict", help="标记冲突并冻结提升")
    mark.add_argument("path")
    mark.add_argument("--reason", required=True)
    add_actor_options(mark, ("contributor", "maintainer"))
    mark.set_defaults(func=cmd_mark_conflict)

    resolve = subparsers.add_parser("resolve-conflict", help="Maintainer 裁决冲突")
    resolve.add_argument("path")
    resolve.add_argument("--resolution", required=True)
    add_actor_options(resolve, ("maintainer",))
    resolve.set_defaults(func=cmd_resolve_conflict)

    lint = subparsers.add_parser("lint", help="检查条目、证据、成熟度、目录和索引")
    lint.add_argument("--fix", action="store_true", help="执行成熟度衰减、归档和索引更新")
    lint.add_argument("--as-of", help="以指定 ISO 8601 时间执行检查")
    lint.add_argument("--actor", default="knowledge-lint")
    lint.add_argument("--role", default="reader", choices=sorted(ROLES))
    lint.add_argument("--session", default="manual")
    lint.set_defaults(func=cmd_lint)

    index = subparsers.add_parser("reindex", help="重建受治理的目录区块")
    add_actor_options(index, ("maintainer", "system"))
    index.set_defaults(func=cmd_reindex)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (GovernanceError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
