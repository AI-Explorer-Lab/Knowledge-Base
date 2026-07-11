from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

from .catalog import build_catalogs
from .errors import KnowledgeError
from .evidence import append_event, utc_now
from .lifecycle import derived_dates, evaluate
from .repository import Repository
from .validator import validate
from .yaml_io import atomic_write, dump_yaml


def _root(value: str) -> Path:
    return Path(value).resolve()


def command_lint(args: argparse.Namespace) -> int:
    repo = Repository(args.root)
    findings = validate(args.root, repo.load_knowledge(), repo.load_evidence())
    for finding in findings:
        print(finding.render())
    errors = sum(item.severity == "error" for item in findings)
    print(f"检查完成：{errors} 个错误，{len(findings) - errors} 个警告")
    return 1 if errors else 0


def command_catalog(args: argparse.Namespace) -> int:
    repo = Repository(args.root)
    paths = build_catalogs(args.root, repo.load_knowledge(), repo.load_evidence(), repo.policy("review"))
    for path in paths:
        print(path.relative_to(args.root))
    return 0


def command_event(args: argparse.Namespace) -> int:
    repo = Repository(args.root)
    if args.id not in {item.id for item in repo.load_knowledge()}:
        raise KnowledgeError(f"知识 ID 不存在：{args.id}")
    event: Dict[str, Any] = {"event_id": args.event_id or f"EVT-{uuid.uuid4().hex[:16].upper()}", "event_type": args.type, "occurred_at": args.occurred_at or utc_now(), "contributor": args.contributor}
    for key in ("project", "scenario_id", "evidence_group_id", "validation_method", "result_summary", "reference", "operator", "supersedes_event_id", "revokes_event_id"):
        value = getattr(args, key, None)
        if value:
            event[key] = value
    required = ("project", "scenario_id", "evidence_group_id", "validation_method", "result_summary", "reference")
    if args.type in {"validated_success", "validated_failure"}:
        missing = [key for key in required if key not in event]
        if missing:
            raise KnowledgeError("验证事件缺少字段：" + ", ".join(missing))
    changed = append_event(args.root, args.id, event)
    print("事件已追加" if changed else "事件已存在，幂等跳过")
    return 0


def _evaluations(repo: Repository, today: dt.date) -> List[Dict[str, Any]]:
    evidence = repo.load_evidence()
    review = repo.policy("review")
    maturity = repo.policy("maturity")
    result = []
    for record in repo.load_knowledge():
        events = evidence.get(record.id).events if record.id in evidence else []
        proposals = evaluate(record.metadata, events, review, maturity, today)
        if proposals:
            result.append({"knowledge_id": record.id, "path": str(record.path.relative_to(repo.root)), "derived": derived_dates(record.metadata, events, review), "proposals": proposals})
    return result


def command_evaluate(args: argparse.Namespace) -> int:
    result = _evaluations(Repository(args.root), dt.date.fromisoformat(args.today) if args.today else dt.date.today())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_propose(args: argparse.Namespace) -> int:
    repo = Repository(args.root)
    items = [item for item in _evaluations(repo, dt.date.fromisoformat(args.today) if args.today else dt.date.today()) if item["knowledge_id"] == args.id]
    if not items:
        print("当前没有可提出的状态变更")
        return 0
    output = args.root / "contributions" / "pending" / f"{args.id}-{dt.date.today().isoformat()}.yaml"
    data = {"schema_version": 1, "proposal_id": f"TR-{uuid.uuid4().hex[:12].upper()}", "created_at": utc_now(), **items[0], "approval_required": True}
    atomic_write(output, dump_yaml(data))
    print(output.relative_to(args.root))
    return 0


def command_web(args: argparse.Namespace) -> int:
    import uvicorn

    from .web.main import create_app

    app = create_app(args.root, args.environment)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="knowledge", description="Git 知识库治理工具")
    result.add_argument("--root", type=_root, default=Path.cwd(), help="知识库根目录")
    commands = result.add_subparsers(dest="command", required=True)
    lint = commands.add_parser("lint", help="校验知识、证据和引用")
    lint.set_defaults(func=command_lint)
    catalog = commands.add_parser("build-catalog", help="生成确定性 Catalog 和报告")
    catalog.set_defaults(func=command_catalog)
    event = commands.add_parser("record-event", help="幂等追加证据事件")
    event.add_argument("--id", required=True)
    event.add_argument("--type", required=True, choices=["referenced", "adopted", "validated_success", "validated_failure", "not_applicable", "contradiction_found", "review_completed", "deprecated", "archived", "event_correction", "event_revoked"])
    event.add_argument("--event-id")
    event.add_argument("--occurred-at")
    event.add_argument("--contributor", required=True)
    for option in ("project", "scenario-id", "evidence-group-id", "validation-method", "result-summary", "reference", "operator", "supersedes-event-id", "revokes-event-id"):
        event.add_argument(f"--{option}")
    event.set_defaults(func=command_event)
    lifecycle = commands.add_parser("evaluate-lifecycle", help="输出生命周期和成熟度候选")
    lifecycle.add_argument("--today")
    lifecycle.set_defaults(func=command_evaluate)
    proposal = commands.add_parser("propose-transition", help="生成状态变更提案")
    proposal.add_argument("--id", required=True)
    proposal.add_argument("--today")
    proposal.set_defaults(func=command_propose)
    web = commands.add_parser("web", help="启动本地知识管理网页")
    web.add_argument("--host", default="127.0.0.1", help="监听地址，默认只允许本机访问")
    web.add_argument("--port", type=int, default=8000, help="监听端口")
    web.add_argument("--environment", default="development", choices=["development", "testing"])
    web.set_defaults(func=command_web)
    return result


def main(argv: List[str] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return args.func(args)
    except KnowledgeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
