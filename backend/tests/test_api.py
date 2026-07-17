from __future__ import annotations

import hashlib
import hmac
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import yaml
from fastapi.testclient import TestClient

from tools import knowledge_governance as governance
from backend.config.config import load_environment
from backend.database import session as database_session
from backend.database.lifecycle import close_database, init_database
from backend.domain.req import KnowledgeInput, ManualKnowledgeRequest, MemberCreate
from backend.main import create_app
from backend.mapper import database_system_state
from backend.service.member_service import MemberService
from backend.service.repository_lock import RepositoryWriteLock
import backend.service.preview_token_service as preview_token_module


PREVIEW_SECRET = b"preview-test-secret-32-bytes-long!!"
IDENTITY_SECRET = b"identity-test-secret-32-bytes-long!"


def config_data():
    return {
        "version": 1,
        "members": [
            {
                "id": "zhangsan",
                "display_name": "张三",
                "role": "maintainer",
                "status": "active",
            },
            {
                "id": "lisi",
                "display_name": "李四",
                "role": "contributor",
                "status": "active",
            },
            {
                "id": "wangwu",
                "display_name": "王五",
                "role": "reader",
                "status": "active",
            },
        ],
        "knowledge_options": {
            "business_domains": ["finance"],
        },
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "knowledge-catalog.md").write_text("# 测试知识库\n", encoding="utf-8")
    (tmp_path / "log.md").write_text("# 知识贡献日志\n", encoding="utf-8")
    (tmp_path / ".knowledge-config.yaml").write_text(
        yaml.safe_dump(config_data(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (tmp_path / "tech-wiki").mkdir()
    (tmp_path / "team-conventions").mkdir()
    (tmp_path / "team-conventions" / "coding-standards.md").write_text(
        "# 既有团队规范\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "knowledge").mkdir(parents=True)
    (tmp_path / "biz-wiki" / "finance").mkdir(parents=True)
    return tmp_path


def client_for(
    repo: Path,
    actor: str,
    *,
    raise_server_exceptions: bool = True,
    **settings_overrides,
) -> TestClient:
    values = {
        "repo_root": repo,
        "dev_actor": actor,
        "preview_secret": PREVIEW_SECRET,
    }
    values.update(settings_overrides)
    return TestClient(
        create_app(load_environment("test", values)),
        raise_server_exceptions=raise_server_exceptions,
    )


def personal_payload(**updates):
    payload = {
        "scope": "personal",
        "title": "本地 API 端口排查",
        "type": "guideline",
        "tags": ["api", "debug"],
        "source_references": ["个人复盘"],
        "content": "启动服务前，先确认 8000 端口没有被占用。",
    }
    payload.update(updates)
    return payload


def team_payload(**updates):
    payload = {
        "scope": "team",
        "title": "团队治理约定",
        "type": "guideline",
        "tags": ["governance"],
        "source_references": ["架构评审"],
        "layer": "layer1",
        "technical_direction": "patterns",
        "content": "所有人工注入都必须先预览。",
    }
    payload.update(updates)
    if payload.get("layer") != "layer1" and "technical_direction" not in updates:
        payload.pop("technical_direction", None)
    return payload


def test_development_identity_is_fixed_and_reader_cannot_create(repo: Path):
    lisi = client_for(repo, "lisi")
    response = lisi.get(
        "/api/me",
        headers={"X-Knowledge-Actor": "zhangsan", "X-Role": "maintainer"},
    )
    assert response.status_code == 200
    assert response.json()["member"]["id"] == "lisi"
    assert response.json()["member"]["role"] == "contributor"

    reader = client_for(repo, "wangwu")
    denied = reader.get(
        "/api/knowledge/options",
        headers={"X-Request-ID": "permission-denied-123"},
    )
    assert denied.status_code == 403
    assert denied.headers["X-Request-ID"] == "permission-denied-123"
    assert reader.post("/api/knowledge/preview", json=personal_payload()).status_code == 403


def test_knowledge_templates_are_controlled_and_role_protected(repo: Path):
    contributor = client_for(repo, "lisi")
    template_dir = Path(__file__).resolve().parents[1] / "template"
    filenames = {
        "model": "model.md",
        "decision": "decision.md",
        "guideline": "guideline.md",
        "pitfall": "pitfall.md",
        "process": "process.md",
    }

    for knowledge_type, filename in filenames.items():
        response = contributor.get(f"/api/knowledge/templates/{knowledge_type}")
        assert response.status_code == 200, response.text
        assert response.json() == {
            "type": knowledge_type,
            "technical_direction": None,
            "content": (template_dir / filename).read_text(encoding="utf-8"),
        }
        assert response.json()["content"].startswith("## ")
        assert not any(
            line.startswith("# ") for line in response.json()["content"].splitlines()
        )

    invalid = contributor.get("/api/knowledge/templates/../../README.md")
    assert invalid.status_code in {404, 422}

    unsupported = contributor.get("/api/knowledge/templates/unknown")
    assert unsupported.status_code == 422

    base_content = (template_dir / "guideline.md").read_text(encoding="utf-8")
    direction_files = {
        "patterns": "pattern.md",
        "anti-patterns": "anti-pattern.md",
    }
    for technical_direction, filename in direction_files.items():
        direction_content = (template_dir / filename).read_text(encoding="utf-8")
        response = contributor.get(
            "/api/knowledge/templates/guideline",
            params={"technical_direction": technical_direction},
        )
        assert response.status_code == 200, response.text
        assert response.json() == {
            "type": "guideline",
            "technical_direction": technical_direction,
            "content": f"{direction_content.rstrip()}\n\n{base_content.lstrip()}",
        }

    invalid_direction = contributor.get(
        "/api/knowledge/templates/guideline",
        params={"technical_direction": "unknown"},
    )
    assert invalid_direction.status_code == 422

    reader = client_for(repo, "wangwu")
    assert reader.get("/api/knowledge/templates/guideline").status_code == 403


def test_knowledge_template_missing_or_empty_returns_clear_error(repo: Path):
    contributor = client_for(repo, "lisi", raise_server_exceptions=False)
    isolated_templates = repo / "templates"
    isolated_templates.mkdir()
    contributor.app.state.knowledge_templates.template_dir = isolated_templates

    missing = contributor.get("/api/knowledge/templates/guideline")
    assert missing.status_code == 500
    assert missing.json()["detail"]["code"] == "knowledge_template_unavailable"

    (isolated_templates / "guideline.md").write_text("   \n", encoding="utf-8")
    empty = contributor.get("/api/knowledge/templates/guideline")
    assert empty.status_code == 500
    assert empty.json()["detail"]["code"] == "knowledge_template_empty"

    (isolated_templates / "guideline.md").write_text("## 指南\n", encoding="utf-8")
    missing_direction = contributor.get(
        "/api/knowledge/templates/guideline",
        params={"technical_direction": "patterns"},
    )
    assert missing_direction.status_code == 500
    assert missing_direction.json()["detail"]["code"] == "knowledge_template_unavailable"

    (isolated_templates / "pattern.md").write_text("\n", encoding="utf-8")
    empty_direction = contributor.get(
        "/api/knowledge/templates/guideline",
        params={"technical_direction": "patterns"},
    )
    assert empty_direction.status_code == 500
    assert empty_direction.json()["detail"]["code"] == "knowledge_template_empty"


def test_health_lifespan_database_and_request_id(repo: Path):
    runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "dev_actor": "zhangsan",
        },
    )
    with TestClient(create_app(runtime)) as client:
        response = client.get("/api/health", headers={"X-Request-ID": "test-request-123"})
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "service": "knowledge-base-backend",
            "database": "ready",
            "repository": "ready",
        }
        assert response.headers["X-Request-ID"] == "test-request-123"


def test_lifespan_rejects_unknown_local_actor_and_respects_create_tables_flag(repo: Path):
    unknown_actor_runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "dev_actor": "missing-member",
        },
    )
    with pytest.raises(Exception, match="当前身份不在团队成员配置中"):
        with TestClient(create_app(unknown_actor_runtime)):
            pass

    database_path = repo / "no-auto-schema.db"
    no_schema_runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "dev_actor": "zhangsan",
            "database_url": f"sqlite+aiosqlite:///{database_path}",
            "database_create_tables": False,
        },
    )
    with TestClient(create_app(no_schema_runtime)) as client:
        assert client.get("/api/health").status_code == 200
    with sqlite3.connect(database_path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    assert tables == []


def test_personal_preview_create_idempotent_retry_and_by_id_view(repo: Path):
    lisi = client_for(repo, "lisi")
    preview_response = lisi.post("/api/knowledge/preview", json=personal_payload())
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert len(preview["checks"]) == 6
    assert all(item["status"] == "passed" for item in preview["checks"])
    assert preview["preview"]["id"] == "PK-LI-GDL-001"
    assert preview["preview"]["owner_id"] == "lisi"
    assert preview["preview"]["layer"] == "layer0p"
    assert preview["preview"]["content"] == personal_payload()["content"]
    assert preview["preview"]["relative_path"].startswith(
        "personal-prefernece/lisi/knowledge/guidelines/"
    )

    changed = personal_payload(title="已修改的标题", preview_token=preview["preview_token"])
    rejected = lisi.post("/api/knowledge/manual", json=changed)
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "preview_form_changed"

    request = personal_payload(preview_token=preview["preview_token"])
    created = lisi.post("/api/knowledge/manual", json=request)
    assert created.status_code == 201, created.text
    result = created.json()
    assert result["knowledge"]["type"] == "guideline"
    assert result["knowledge"]["source_references"] == ["个人复盘"]
    assert result["actor"] == {"id": "lisi", "display_name": "李四", "role": "contributor"}
    assert [item["key"] for item in result["writes"]] == [
        "knowledge_file",
        "layer_catalog",
        "global_catalog",
        "audit_log",
    ]
    path = repo / result["knowledge"]["relative_path"]
    assert path.is_file()
    metadata, _body = governance.read_entry(path)
    assert metadata["maturity"] == "draft"
    assert metadata["owner_id"] == "lisi"
    assert result["knowledge"]["id"] in (
        repo / "personal-prefernece" / "lisi" / "knowledge" / "catalog.md"
    ).read_text(encoding="utf-8")
    assert "| Layer 0-P | 1 | 0 |" in (repo / "knowledge-catalog.md").read_text(
        encoding="utf-8"
    )

    replay = lisi.post("/api/knowledge/manual", json=request)
    assert replay.status_code == 201
    assert replay.json()["idempotent_replay"] is True
    assert (repo / "log.md").read_text(encoding="utf-8").count("`create`") == 1

    content_before_view = path.read_bytes()
    mtime_before_view = path.stat().st_mtime_ns
    evidence_before_view = governance.read_entry(path)[0]["evidence"]
    own_view = lisi.get(f"/api/knowledge/{result['knowledge']['id']}")
    assert own_view.status_code == 200
    assert own_view.json()["knowledge"]["content"] == personal_payload()["content"]
    own_review = own_view.json()["knowledge"]["review"]
    assert own_review["next_review_at"].endswith("+08:00")
    assert own_review["overdue"] is False
    assert (
        governance.parse_time(own_review["next_review_at"])
        - governance.parse_time(result["knowledge"]["created_at"])
    ).days == 30
    teammate_view = client_for(repo, "zhangsan").get(
        f"/api/knowledge/{result['knowledge']['id']}"
    )
    assert teammate_view.status_code == 200
    assert teammate_view.json()["knowledge"]["review"] == own_review
    assert path.read_bytes() == content_before_view
    assert path.stat().st_mtime_ns == mtime_before_view
    assert governance.read_entry(path)[0]["evidence"] == evidence_before_view

    reader = client_for(repo, "wangwu")
    listing = reader.get("/api/knowledge", params={"layer": "layer0p"})
    assert listing.status_code == 200, listing.text
    listing_data = listing.json()
    assert listing_data["total"] == 1
    assert listing_data["counts"] == {
        "layer0p": 1,
        "layer0t": 0,
        "layer1": 0,
        "layer2": 0,
        "layer3": 0,
    }
    assert listing_data["items"][0] == {
        "id": result["knowledge"]["id"],
        "title": personal_payload()["title"],
        "type": "guideline",
        "scope": "personal",
        "owner_id": "lisi",
        "layer": "layer0p",
        "technical_direction": None,
        "maturity": "draft",
        "created_at": result["knowledge"]["created_at"],
        "tags": ["api", "debug"],
        "relative_path": result["knowledge"]["relative_path"],
        "excerpt": personal_payload()["content"],
        "review": own_review,
    }
    search = reader.get("/api/knowledge", params={"q": "端口排查"})
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert reader.get("/api/knowledge", params={"layer": "unknown"}).status_code == 422
    assert path.read_bytes() == content_before_view
    assert governance.read_entry(path)[0]["evidence"] == evidence_before_view


def test_actor_form_and_storage_fields_cannot_be_forged(repo: Path):
    lisi = client_for(repo, "lisi")
    forged = personal_payload(owner_id="zhangsan", actor="zhangsan", role="maintainer")
    response = lisi.post("/api/knowledge/preview", json=forged)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"

    category_forgery = lisi.post(
        "/api/knowledge/preview",
        json=personal_payload(category="guidelines"),
    )
    assert category_forgery.status_code == 422

    traversal = lisi.post(
        "/api/knowledge/preview",
        json=team_payload(category="arbitrary-folder", path="/tmp/escape.md"),
    )
    assert traversal.status_code == 422


def test_team_layer_domain_whitelist_and_actor_bound_token(repo: Path):
    lisi = client_for(repo, "lisi")
    layer2 = team_payload(layer="layer2", domain="finance")
    preview = lisi.post("/api/knowledge/preview", json=layer2)
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["preview"]["relative_path"].startswith("biz-wiki/finance/guidelines/")

    unknown_domain = lisi.post(
        "/api/knowledge/preview",
        json=team_payload(layer="layer2", domain="unknown"),
    )
    assert unknown_domain.status_code == 422
    assert unknown_domain.json()["detail"]["code"] == "invalid_domain"

    other_actor = client_for(repo, "zhangsan")
    submit = {**layer2, "preview_token": data["preview_token"]}
    denied = other_actor.post("/api/knowledge/manual", json=submit)
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "preview_actor_mismatch"


def test_technical_direction_is_optional_and_only_allowed_for_layer1(repo: Path):
    client = client_for(repo, "lisi")
    missing = team_payload()
    missing.pop("technical_direction")
    response = client.post("/api/knowledge/preview", json=missing)
    assert response.status_code == 200, response.text
    assert response.json()["preview"]["technical_direction"] is None
    assert response.json()["preview"]["relative_path"].startswith(
        "tech-wiki/guidelines/"
    )

    misplaced = client.post(
        "/api/knowledge/preview",
        json=team_payload(layer="layer2", domain="finance", technical_direction="patterns"),
    )
    assert misplaced.status_code == 422


def test_neutral_layer1_knowledge_can_complete_preview_and_create(repo: Path):
    client = client_for(repo, "lisi")
    payload = team_payload()
    payload.pop("technical_direction")

    preview = client.post("/api/knowledge/preview", json=payload)
    assert preview.status_code == 200, preview.text
    created = client.post(
        "/api/knowledge/manual",
        json={**payload, "preview_token": preview.json()["preview_token"]},
    )
    assert created.status_code == 201, created.text
    knowledge = created.json()["knowledge"]
    assert knowledge["technical_direction"] is None
    assert knowledge["id"] == "TK-GDL-001"
    assert knowledge["relative_path"].startswith("tech-wiki/guidelines/")
    metadata, _body = governance.read_entry(repo / knowledge["relative_path"])
    assert "technical_direction" not in metadata


@pytest.mark.parametrize("technical_direction", [None, "patterns", "anti-patterns"])
def test_layer1_direction_is_optional_metadata_not_path_or_id(
    repo: Path,
    technical_direction: str | None,
):
    payload = team_payload()
    if technical_direction is None:
        payload.pop("technical_direction")
    else:
        payload["technical_direction"] = technical_direction
    response = client_for(repo, "lisi").post(
        "/api/knowledge/preview",
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.json()["preview"]["id"] == "TK-GDL-001"
    assert response.json()["preview"]["relative_path"].startswith(
        "tech-wiki/guidelines/"
    )
    assert response.json()["preview"]["technical_direction"] == technical_direction
    metadata = response.json()["preview"]["metadata"]
    if technical_direction is None:
        assert "technical_direction" not in metadata
    else:
        assert metadata["technical_direction"] == technical_direction


@pytest.mark.parametrize(
    ("knowledge_type", "directory"),
    [
        ("model", "models"),
        ("decision", "decisions"),
        ("guideline", "guidelines"),
        ("pitfall", "pitfalls"),
        ("process", "processes"),
    ],
)
def test_team_directory_is_derived_from_knowledge_type(
    repo: Path,
    knowledge_type: str,
    directory: str,
):
    response = client_for(repo, "lisi").post(
        "/api/knowledge/preview",
        json=team_payload(type=knowledge_type, layer="layer3"),
    )
    assert response.status_code == 200, response.text
    assert response.json()["preview"]["relative_path"].startswith(
        f"docs/knowledge/{directory}/"
    )


def test_layer2_option_remains_visible_when_no_business_domain_is_configured(repo: Path):
    config = config_data()
    config["knowledge_options"]["business_domains"] = []
    (repo / ".knowledge-config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    response = client_for(repo, "lisi").get("/api/knowledge/options")
    assert response.status_code == 200
    assert "layer2" in {item["value"] for item in response.json()["layers"]}
    assert response.json()["layers"][0] == {
        "value": "layer0t",
        "label": "Layer 0-T 团队约定",
    }
    assert response.json()["business_domains"] == []
    assert response.json()["technical_directions"] == [
        {"value": "patterns", "label": "正向模式"},
        {"value": "anti-patterns", "label": "反模式"},
    ]
    assert "categories" not in response.json()


def test_maintainer_can_create_business_domain_and_options_refresh(repo: Path):
    config = config_data()
    config["knowledge_options"]["business_domains"] = []
    (repo / ".knowledge-config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    maintainer = client_for(repo, "zhangsan")

    created = maintainer.post(
        "/api/business-domains",
        json={
            "id": "order",
            "name": "订单",
            "description": "订单履约与交易过程",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["business_domain"] == {
        "id": "order",
        "name": "订单",
        "description": "订单履约与交易过程",
        "status": "active",
    }

    options = maintainer.get("/api/knowledge/options")
    assert options.status_code == 200
    assert options.json()["business_domains"] == [created.json()["business_domain"]]
    persisted = yaml.safe_load((repo / ".knowledge-config.yaml").read_text(encoding="utf-8"))
    assert persisted["knowledge_options"]["business_domains"] == [
        created.json()["business_domain"]
    ]
    assert not (repo / "biz-wiki" / "order").exists()
    audit_log = (repo / "log.md").read_text(encoding="utf-8")
    assert "business-domain-create" in audit_log
    assert "web:business-domains" in audit_log

    duplicate = maintainer.post(
        "/api/business-domains",
        json={"id": "order", "name": "重复订单", "description": ""},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "business_domain_exists"


def test_only_maintainer_can_create_safe_business_domain(repo: Path):
    contributor = client_for(repo, "lisi")
    denied = contributor.post(
        "/api/business-domains",
        json={"id": "order", "name": "订单", "description": ""},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "permission_denied"

    maintainer = client_for(repo, "zhangsan")
    for unsafe_id in ["archive", "Order", "../order"]:
        invalid = maintainer.post(
            "/api/business-domains",
            json={"id": unsafe_id, "name": "订单", "description": ""},
        )
        assert invalid.status_code == 422


@pytest.mark.parametrize(
    ("payload", "expected_id", "path_prefix", "layer_catalog", "layer_summary"),
    [
        (
            team_payload(layer="layer0t"),
            "TC-GDL-001",
            "team-conventions/guidelines/",
            "team-conventions/catalog.md",
            "Layer 0-T",
        ),
        (
            team_payload(layer="layer1"),
            "TK-GDL-001",
            "tech-wiki/guidelines/",
            "tech-wiki/catalog.md",
            "Layer 1",
        ),
        (
            team_payload(layer="layer2", domain="finance"),
            "BK-GDL-001",
            "biz-wiki/finance/guidelines/",
            "biz-wiki/finance/catalog.md",
            "Layer 2",
        ),
        (
            team_payload(layer="layer3"),
            "PJ-GDL-001",
            "docs/knowledge/guidelines/",
            "docs/knowledge/catalog.md",
            "Layer 3",
        ),
    ],
)
def test_team_manual_commit_updates_entry_catalogs_and_log(
    repo: Path,
    payload: dict,
    expected_id: str,
    path_prefix: str,
    layer_catalog: str,
    layer_summary: str,
):
    client = client_for(repo, "lisi")
    preview = client.post("/api/knowledge/preview", json=payload)
    assert preview.status_code == 200, preview.text

    created = client.post(
        "/api/knowledge/manual",
        json={**payload, "preview_token": preview.json()["preview_token"]},
    )
    assert created.status_code == 201, created.text
    knowledge = created.json()["knowledge"]
    assert knowledge["id"] == expected_id
    assert knowledge["scope"] == "team"
    assert knowledge["owner_id"] is None
    assert knowledge["technical_direction"] == payload.get("technical_direction")
    assert knowledge["relative_path"].startswith(path_prefix)
    knowledge_path = repo / knowledge["relative_path"]
    assert knowledge_path.is_file()
    metadata, _body = governance.read_entry(knowledge_path)
    if payload.get("technical_direction") is None:
        assert "technical_direction" not in metadata
    else:
        assert metadata["technical_direction"] == payload["technical_direction"]
    assert knowledge["id"] in (repo / layer_catalog).read_text(encoding="utf-8")
    assert f"| {layer_summary} | 1 | 0 |" in (
        repo / "knowledge-catalog.md"
    ).read_text(encoding="utf-8")
    audit = (repo / "log.md").read_text(encoding="utf-8")
    assert f"| `lisi` | `create` | `{knowledge['id']}` |" in audit

    listing = client.get("/api/knowledge", params={"layer": payload["layer"]})
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] == 1
    assert listing.json()["counts"][payload["layer"]] == 1
    assert listing.json()["items"][0]["id"] == knowledge["id"]


def test_preview_token_tampering_and_expiry_are_rejected(
    repo: Path,
    monkeypatch,
):
    client = client_for(repo, "lisi")
    preview = client.post("/api/knowledge/preview", json=personal_payload()).json()
    payload_part, signature = preview["preview_token"].split(".", 1)
    replacement = "A" if signature[0] != "A" else "B"
    tampered = f"{payload_part}.{replacement}{signature[1:]}"
    tampered_response = client.post(
        "/api/knowledge/manual",
        json=personal_payload(preview_token=tampered),
    )
    assert tampered_response.status_code == 400
    assert tampered_response.json()["detail"]["code"] == "invalid_preview_token"

    real_now = time.time()
    monkeypatch.setattr(
        preview_token_module,
        "time",
        SimpleNamespace(time=lambda: real_now + 301),
    )
    expired_response = client.post(
        "/api/knowledge/manual",
        json=personal_payload(preview_token=preview["preview_token"]),
    )
    assert expired_response.status_code == 409
    assert expired_response.json()["detail"]["code"] == "preview_expired"


def test_completed_preview_replays_after_expiry_without_duplicate_write(
    repo: Path,
    monkeypatch,
):
    client = client_for(repo, "lisi")
    preview = client.post("/api/knowledge/preview", json=personal_payload()).json()
    request = personal_payload(preview_token=preview["preview_token"])
    created = client.post("/api/knowledge/manual", json=request)
    assert created.status_code == 201
    knowledge_id = created.json()["knowledge"]["id"]

    real_now = time.time()
    monkeypatch.setattr(
        preview_token_module,
        "time",
        SimpleNamespace(time=lambda: real_now + 301),
    )
    replay = client.post("/api/knowledge/manual", json=request)
    assert replay.status_code == 201
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["knowledge"]["id"] == knowledge_id
    assert (repo / "log.md").read_text(encoding="utf-8").count("`create`") == 1
    matching_files = [
        path
        for path in repo.rglob("*.md")
        if governance.is_entry_file(path)
        and governance.read_entry(path)[0].get("id") == knowledge_id
    ]
    assert len(matching_files) == 1


def test_failed_repository_write_releases_preview_for_retry(repo: Path, monkeypatch):
    client = client_for(repo, "lisi", raise_server_exceptions=False)
    preview = client.post("/api/knowledge/preview", json=personal_payload()).json()
    request = personal_payload(preview_token=preview["preview_token"])
    original_create = governance.create_knowledge_entry
    attempts = 0

    def fail_once(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("temporary repository failure")
        return original_create(**kwargs)

    monkeypatch.setattr(governance, "create_knowledge_entry", fail_once)
    failed = client.post("/api/knowledge/manual", json=request)
    assert failed.status_code == 500

    retried = client.post("/api/knowledge/manual", json=request)
    assert retried.status_code == 201, retried.text
    assert retried.json()["idempotent_replay"] is False
    assert (repo / "log.md").read_text(encoding="utf-8").count("`create`") == 1


def test_member_disable_takes_effect_before_preview_commit(repo: Path):
    contributor = client_for(repo, "lisi")
    preview = contributor.post("/api/knowledge/preview", json=personal_payload()).json()
    maintainer = client_for(repo, "zhangsan")
    disabled = maintainer.patch("/api/members/lisi", json={"status": "disabled"})
    assert disabled.status_code == 200

    submit = contributor.post(
        "/api/knowledge/manual",
        json=personal_payload(preview_token=preview["preview_token"]),
    )
    assert submit.status_code == 403
    assert submit.json()["detail"]["code"] == "member_disabled"


def test_concurrent_same_preview_writes_once_and_replays_idempotently(repo: Path):
    runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "dev_actor": "lisi",
        },
    )
    app = create_app(runtime)
    actor = app.state.members.get_member("lisi")
    draft = KnowledgeInput(**personal_payload())
    preview = app.state.knowledge.preview(draft, actor)
    request = ManualKnowledgeRequest(
        **personal_payload(),
        preview_token=preview["preview_token"],
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: app.state.knowledge.create(request, actor), range(2)))

    assert sorted(result.get("idempotent_replay", False) for result in results) == [False, True]
    knowledge_id = results[0]["knowledge"]["id"]
    assert results[1]["knowledge"]["id"] == knowledge_id
    assert (repo / "log.md").read_text(encoding="utf-8").count("`create`") == 1
    matching_files = [
        path
        for path in repo.rglob("*.md")
        if governance.is_entry_file(path) and governance.read_entry(path)[0].get("id") == knowledge_id
    ]
    assert len(matching_files) == 1


def test_concurrent_distinct_writes_preserve_both_catalog_and_audit_entries(repo: Path):
    runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "dev_actor": "lisi",
        },
    )
    app = create_app(runtime)
    actor = app.state.members.get_member("lisi")
    payloads = [
        personal_payload(title="并发知识 A"),
        personal_payload(title="并发知识 B"),
    ]
    previews = [
        app.state.knowledge.preview(KnowledgeInput(**payload), actor)
        for payload in payloads
    ]
    requests = [
        ManualKnowledgeRequest(**payload, preview_token=preview["preview_token"])
        for payload, preview in zip(payloads, previews)
    ]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda request: app.state.knowledge.create(request, actor), requests))

    knowledge_ids = {result["knowledge"]["id"] for result in results}
    assert len(knowledge_ids) == 2
    personal_catalog = (
        repo / "personal-prefernece" / "lisi" / "knowledge" / "catalog.md"
    ).read_text(encoding="utf-8")
    assert all(knowledge_id in personal_catalog for knowledge_id in knowledge_ids)
    assert (repo / "log.md").read_text(encoding="utf-8").count("`create`") == 2
    assert "| Layer 0-P | 2 | 0 |" in (repo / "knowledge-catalog.md").read_text(
        encoding="utf-8"
    )


def test_member_permissions_last_maintainer_and_case_insensitive_ids(repo: Path):
    maintainer = client_for(repo, "zhangsan")
    reader = client_for(repo, "wangwu")
    assert reader.get("/api/members").status_code == 403
    assert maintainer.get("/api/members").status_code == 200

    duplicate = maintainer.post(
        "/api/members",
        json={"id": "ZHANGSAN", "display_name": "重复", "role": "reader"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "member_exists"

    protected = maintainer.patch("/api/members/zhangsan", json={"role": "reader"})
    assert protected.status_code == 409
    assert protected.json()["detail"]["code"] == "last_maintainer_protected"

    created = maintainer.post(
        "/api/members",
        json={"id": "Alice", "display_name": "Alice", "role": "maintainer"},
    )
    assert created.status_code == 201
    assert created.json()["member"]["id"] == "alice"
    demoted = maintainer.patch("/api/members/zhangsan", json={"role": "reader"})
    assert demoted.status_code == 200

    no_longer_allowed = maintainer.patch("/api/members/alice", json={"role": "reader"})
    assert no_longer_allowed.status_code == 403
    log = (repo / "log.md").read_text(encoding="utf-8")
    assert "`member-create`" in log
    assert "`member-update`" in log


def test_production_requires_stable_secrets_and_signed_identity(repo: Path):
    with pytest.raises(ValueError, match="stable KNOWLEDGE_AGENT__PREVIEW_SECRET"):
        load_environment(
            "production",
            {
                "repo_root": repo,
                "preview_secret": b"",
                "identity_hmac_secret": IDENTITY_SECRET,
            },
        )

    app = create_app(
        load_environment(
            "production",
            {
                "repo_root": repo,
                "preview_secret": PREVIEW_SECRET,
                "identity_hmac_secret": IDENTITY_SECRET,
            },
        )
    )
    client = TestClient(app)
    assert client.get("/api/me").status_code == 401
    timestamp = int(time.time())
    actor = "lisi"
    signature = hmac.new(
        IDENTITY_SECRET,
        f"{timestamp}:{actor}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    response = client.get(
        "/api/me",
        headers={
            "X-Knowledge-Actor": actor,
            "X-Knowledge-Timestamp": str(timestamp),
            "X-Knowledge-Signature": signature,
        },
    )
    assert response.status_code == 200
    assert response.json()["member"]["role"] == "contributor"


def test_relative_sqlite_path_is_anchored_to_repository(repo: Path):
    relative = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "database_url": "sqlite+aiosqlite:///runtime/backend.db",
        },
    )
    assert relative.database_url == f"sqlite+aiosqlite:///{repo / 'runtime' / 'backend.db'}"

    memory = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "database_url": "sqlite+aiosqlite:///:memory:",
        },
    )
    assert memory.database_url == "sqlite+aiosqlite:///:memory:"


def test_create_rolls_back_entry_catalogs_and_log_on_audit_failure(repo: Path, monkeypatch):
    target = repo / "personal-prefernece" / "lisi" / "knowledge" / "guidelines" / "PK-X.md"
    catalog_before = (repo / "knowledge-catalog.md").read_text(encoding="utf-8")
    log_before = (repo / "log.md").read_text(encoding="utf-8")

    def fail_log(*_args, **_kwargs):
        raise OSError("simulated log failure")

    monkeypatch.setattr(governance, "append_log", fail_log)
    with pytest.raises(OSError, match="simulated"):
        governance.create_knowledge_entry(
            repo=repo,
            path=target,
            knowledge_id="PK-X",
            title="回滚测试",
            knowledge_type="guideline",
            layer="layer0p",
            scope="personal",
            sources=["测试"],
            content="内容",
            actor="lisi",
            role="contributor",
            owner_id="lisi",
        )
    assert not target.exists()
    assert (repo / "knowledge-catalog.md").read_text(encoding="utf-8") == catalog_before
    assert (repo / "log.md").read_text(encoding="utf-8") == log_before
    assert not (target.parents[1] / "catalog.md").exists()


def test_member_config_rolls_back_when_audit_fails(repo: Path, monkeypatch):
    service = MemberService(repo, RepositoryWriteLock(repo))
    before = (repo / ".knowledge-config.yaml").read_text(encoding="utf-8")

    def fail_log(*_args, **_kwargs):
        raise OSError("simulated audit failure")

    monkeypatch.setattr(governance, "append_log", fail_log)
    with pytest.raises(OSError, match="simulated"):
        service.create_member(
            service.get_member("zhangsan"),
            MemberCreate(id="new-member", display_name="New", role="reader"),
        )
    assert (repo / ".knowledge-config.yaml").read_text(encoding="utf-8") == before


def enable_super_admin(repo: Path) -> None:
    config = yaml.safe_load((repo / ".knowledge-config.yaml").read_text(encoding="utf-8"))
    config["members"][0]["role"] = "super_admin"
    (repo / ".knowledge-config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_super_admin_role_update_preview_commit_actions_and_audit(repo: Path):
    enable_super_admin(repo)
    admin = client_for(repo, "zhangsan")
    reader = client_for(repo, "wangwu")

    identity = admin.get("/api/me")
    assert identity.status_code == 200
    assert identity.json()["member"]["role"] == "super_admin"
    assert identity.json()["permissions"] == {
        "can_browse_knowledge": True,
        "can_create_knowledge": True,
        "can_manage_members": True,
        "can_manage_business_domains": True,
        "can_super_admin": True,
    }
    assert reader.get("/api/super-admin/knowledge").status_code == 403
    assert admin.post(
        "/api/members",
        json={"id": "root-two", "display_name": "Root", "role": "super_admin"},
    ).status_code == 422
    protected = admin.patch(
        "/api/members/zhangsan",
        json={"status": "disabled"},
    )
    assert protected.status_code == 403
    assert protected.json()["detail"]["code"] == "super_admin_config_only"

    preview = admin.post("/api/knowledge/preview", json=team_payload())
    assert preview.status_code == 200, preview.text
    created = admin.post(
        "/api/knowledge/manual",
        json={**team_payload(), "preview_token": preview.json()["preview_token"]},
    )
    assert created.status_code == 201, created.text
    knowledge_id = created.json()["knowledge"]["id"]

    detail = admin.get(f"/api/super-admin/knowledge/{knowledge_id}")
    assert detail.status_code == 200, detail.text
    original = detail.json()["knowledge"]
    payload = {
        "scope": "team",
        "title": "修正后的治理决策",
        "type": "decision",
        "tags": ["governance", "corrected"],
        "source_references": ["超级管理员复核"],
        "layer": "layer1",
        "technical_direction": "patterns",
        "content": "修正后的正文必须重新积累当前版本证据。",
        "reason": "修正错误的知识类型和正文",
        "base_digest": original["base_digest"],
    }
    update_preview = admin.post(
        f"/api/super-admin/knowledge/{knowledge_id}/preview",
        json=payload,
    )
    assert update_preview.status_code == 200, update_preview.text
    assert update_preview.json()["after"]["revision"] == 2
    assert update_preview.json()["after"]["maturity"] == "draft"
    assert "relative_path" in update_preview.json()["changed_fields"]

    committed = admin.post(
        f"/api/super-admin/knowledge/{knowledge_id}/commit",
        json={**payload, "preview_token": update_preview.json()["preview_token"]},
        headers={"X-Request-ID": "admin-update-request-001"},
    )
    assert committed.status_code == 200, committed.text
    updated = committed.json()["knowledge"]
    assert updated["revision"] == 2
    assert updated["type"] == "decision"
    assert updated["relative_path"].endswith(f"decisions/{knowledge_id}.md")
    assert not (repo / original["relative_path"]).exists()
    assert (repo / updated["relative_path"]).exists()

    replay = admin.post(
        f"/api/super-admin/knowledge/{knowledge_id}/commit",
        json={**payload, "preview_token": update_preview.json()["preview_token"]},
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True

    archived = admin.post(
        f"/api/super-admin/knowledge/{knowledge_id}/actions",
        json={
            "action": "archive",
            "reason": "该知识暂时不再使用",
        },
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["knowledge"]["archived"] is True
    archived_list = admin.get("/api/super-admin/knowledge", params={"state": "archived"})
    assert any(item["id"] == knowledge_id for item in archived_list.json()["items"])

    restored = admin.post(
        f"/api/super-admin/knowledge/{knowledge_id}/actions",
        json={"action": "restore", "reason": "重新启用该知识"},
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["knowledge"]["archived"] is False

    domain_patch = admin.patch(
        "/api/business-domains/finance",
        json={"name": "财务", "status": "disabled"},
    )
    assert domain_patch.status_code == 200, domain_patch.text
    assert domain_patch.json()["business_domain"]["status"] == "disabled"
    options = admin.get("/api/knowledge/options")
    assert options.status_code == 200
    assert next(item for item in options.json()["business_domains"] if item["id"] == "finance")["status"] == "disabled"

    audit = admin.get("/api/super-admin/audit", params={"q": knowledge_id})
    assert audit.status_code == 200, audit.text
    actions = {item["action"] for item in audit.json()["items"]}
    assert "admin-knowledge-move" in actions
    assert "admin-governance-action" in actions
    log = (repo / "log.md").read_text(encoding="utf-8")
    assert "admin-update-request-001" in log


def test_super_admin_edits_personal_knowledge_without_forging_evidence(repo: Path):
    enable_super_admin(repo)
    personal_path = (
        repo
        / "personal-prefernece"
        / "lisi"
        / "knowledge"
        / "guidelines"
        / "PK-LS-GDL-001.md"
    )
    governance.create_knowledge_entry(
        repo=repo,
        path=personal_path,
        knowledge_id="PK-LS-GDL-001",
        title="李四的排查经验",
        knowledge_type="guideline",
        layer="layer0p",
        scope="personal",
        sources=["李四复盘"],
        content="先检查服务日志。",
        actor="lisi",
        role="contributor",
        owner_id="lisi",
    )
    admin = client_for(repo, "zhangsan")
    detail = admin.get("/api/super-admin/knowledge/PK-LS-GDL-001").json()["knowledge"]
    payload = {
        "scope": "personal",
        "owner_id": "lisi",
        "title": "李四的服务排查经验",
        "type": "guideline",
        "tags": ["debug"],
        "source_references": ["李四复盘"],
        "content": "先检查服务日志，再确认依赖状态。",
        "reason": "补全排查步骤",
        "base_digest": detail["base_digest"],
    }
    preview = admin.post(
        "/api/super-admin/knowledge/PK-LS-GDL-001/preview",
        json=payload,
    )
    assert preview.status_code == 200, preview.text
    committed = admin.post(
        "/api/super-admin/knowledge/PK-LS-GDL-001/commit",
        json={**payload, "preview_token": preview.json()["preview_token"]},
    )
    assert committed.status_code == 200, committed.text
    metadata, _body = governance.read_entry(personal_path)
    assert metadata["owner_id"] == "lisi"
    assert metadata["evidence"]["contributors"] == ["lisi"]
    assert metadata["evidence"]["references"] == []
    assert metadata["evidence"]["validations"] == []


@pytest.mark.asyncio
async def test_mapper_never_commits_and_session_dependency_owns_transaction(
    repo: Path,
    monkeypatch,
):
    database_path = repo / "operations.db"
    runtime = load_environment(
        "test",
        {
            "repo_root": repo,
            "preview_secret": PREVIEW_SECRET,
            "database_url": f"sqlite+aiosqlite:///{database_path}",
        },
    )
    await init_database(runtime)
    try:
        assert database_session.async_session_factory is not None
        async with database_session.async_session_factory() as direct_session:
            commit_spy = AsyncMock()
            monkeypatch.setattr(direct_session, "commit", commit_spy)
            created = await database_system_state.create(
                direct_session,
                {"key": "mapper-only", "value": "created"},
            )
            assert created.key == "mapper-only"
            updated = await database_system_state.update(
                direct_session,
                "mapper-only",
                {"value": "updated"},
            )
            assert updated is not None and updated.value == "updated"
            assert await database_system_state.delete(direct_session, "mapper-only") is True
            assert commit_spy.await_count == 0
            await direct_session.rollback()

        transaction = database_session.get_session()
        managed_session = await anext(transaction)
        await database_system_state.create(
            managed_session,
            {"key": "committed", "value": "yes"},
        )
        with pytest.raises(StopAsyncIteration):
            await anext(transaction)

        async with database_session.async_session_factory() as verification_session:
            committed = await database_system_state.get(verification_session, "committed")
            assert committed is not None and committed.value == "yes"

        rollback_transaction = database_session.get_session()
        rollback_session = await anext(rollback_transaction)
        await database_system_state.create(
            rollback_session,
            {"key": "rolled-back", "value": "no"},
        )
        with pytest.raises(RuntimeError, match="force rollback"):
            await rollback_transaction.athrow(RuntimeError("force rollback"))

        async with database_session.async_session_factory() as verification_session:
            assert await database_system_state.get(verification_session, "rolled-back") is None
    finally:
        await close_database()
