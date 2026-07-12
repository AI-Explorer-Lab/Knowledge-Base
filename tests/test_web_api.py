import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from knowledge_governance.web.main import create_app


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def web_repo(tmp_path):
    root = tmp_path / "knowledge-repo"
    root.mkdir()
    for name in ("schemas", "policies", "templates"):
        shutil.copytree(ROOT / name, root / name)
    shutil.copy(ROOT / ".knowledge-config.yaml", root / ".knowledge-config.yaml")
    for name in ("team-conventions", "tech-wiki", "biz-wiki", "docs/knowledge", "archive", "evidence", "reports", "contributions/pending", "contributions/conflicts"):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "log.md").write_text("# 日志\n\n", encoding="utf-8")
    return root


@pytest.fixture()
def client(web_repo):
    with TestClient(create_app(web_repo, "testing")) as value:
        yield value


def guideline_payload():
    return {
        "title": "接口必须返回稳定错误码",
        "type": "guideline",
        "scope": "tech",
        "domain": "api-design",
        "risk_level": "medium",
        "owner": "platform-team",
        "maintainers": ["backend-team"],
        "applicable_phases": ["ARCHITECT", "IMPLEMENT"],
        "applicable_conditions": ["接口被多个客户端调用"],
        "not_applicable_conditions": ["一次性本地脚本"],
        "tags": ["api", "errors"],
        "source_references": [{"type": "architecture_review", "ref": "review#1"}],
        "polarity": "recommend",
        "sections": {
            "结论": "API 必须返回稳定错误码。",
            "背景与问题": "仅依赖错误文本会导致客户端难以兼容。",
            "适用条件": "接口存在多个调用方。",
            "不适用条件": "无外部调用方的一次性脚本。",
            "详细说明": "错误码表达稳定语义，错误文本用于人类阅读。",
            "验证方式": "接口测试断言错误码。",
            "来源": "架构评审 review#1。",
            "具体行为": "定义并复用错误码枚举。",
            "预期收益": "客户端可以稳定处理异常。",
            "例外情况": "未知异常统一返回内部错误码。",
        },
    }


def test_page_health_and_form_options(client):
    assert client.get("/").status_code == 200
    page = client.get("/").text
    assert "知识列表" in page
    assert 'class="check-grid phase-row"' in page
    assert 'id="applicableConditions" class="auto-grow"' in page
    assert 'id="cancelEdit"' in page
    assert 'id="requestTransition"' in page
    assert 'id="currentMaturity"' in page
    assert '<th>类型</th><th>范围</th><th>成熟度</th>' in page
    assert "<th>领域</th>" not in page
    assert "类型与范围" not in page
    assert client.get("/health").json()["status"] == "ok"
    options = client.get("/api/meta/form-options").json()
    assert options["knowledge_types"] == ["model", "decision", "guideline", "pitfall", "process"]
    assert options["defaults"]["maturity"] == "draft"
    assert options["scopes"] == ["team", "tech", "biz", "project"]
    assert options["phases"][-1] == "ARCHIVE"
    css = client.get("/static/app.css").text
    javascript = client.get("/static/app.js").text
    assert ".message { position: fixed" in css
    assert ".message.fading" in css
    assert "}, 3000);" in javascript


def test_create_and_update_knowledge_through_api(client, web_repo):
    suggested = client.get("/api/knowledge/suggest-id", params={"scope": "tech", "type": "guideline"})
    assert suggested.status_code == 200
    assert suggested.json()["id"] == "TK-GDL-001"

    initial_payload = guideline_payload()
    initial_payload["review_policy_override"] = {"interval": "90d", "reason": "测试保留扩展元数据"}
    response = client.post("/api/knowledge", json=initial_payload, headers={"X-User": "alice"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == "TK-GDL-001"
    assert data["metadata"]["maturity"] == "draft"
    assert data["metadata"]["status"] == "active"
    path = web_repo / "tech-wiki" / "guidelines" / "TK-GDL-001.md"
    assert path.exists()
    assert "## 具体行为" in path.read_text(encoding="utf-8")
    assert "TK-GDL-001" in (web_repo / "knowledge-catalog.md").read_text(encoding="utf-8")

    payload = guideline_payload()
    payload["id"] = "TK-GDL-001"
    payload["title"] = "API 必须返回稳定错误码"
    payload["source_references"].append({"type": "test_report", "ref": "tests#web"})
    update = client.put("/api/knowledge/TK-GDL-001", json=payload, headers={"X-User": "bob"})
    assert update.status_code == 200, update.text
    assert update.json()["metadata"]["title"] == "API 必须返回稳定错误码"
    assert update.json()["metadata"]["maturity"] == "draft"
    assert len(update.json()["metadata"]["source_references"]) == 2
    assert update.json()["metadata"]["review_policy_override"]["interval"] == "90d"


def test_create_project_knowledge_through_api(client, web_repo):
    payload = guideline_payload()
    payload.update({"scope": "project", "domain": "knowledge-base", "title": "项目知识必须随项目保存"})

    suggested = client.get("/api/knowledge/suggest-id", params={"scope": "project", "type": "guideline"})
    assert suggested.status_code == 200
    assert suggested.json()["id"] == "PK-GDL-001"

    response = client.post("/api/knowledge", json=payload)
    assert response.status_code == 200, response.text
    path = web_repo / "docs" / "knowledge" / "guidelines" / "PK-GDL-001.md"
    assert path.exists()
    project_catalog = web_repo / "docs" / "knowledge" / "catalog.md"
    assert "PK-GDL-001" in project_catalog.read_text(encoding="utf-8")


def test_pydantic_rejects_incomplete_type_specific_content(client):
    payload = guideline_payload()
    del payload["sections"]["例外情况"]
    response = client.post("/api/knowledge/validate", json=payload)
    assert response.status_code == 422
    assert "例外情况" in response.text


def test_record_validation_event_and_get_lifecycle_candidate(client, web_repo):
    created = client.post("/api/knowledge", json=guideline_payload())
    knowledge_id = created.json()["id"]
    event = {
        "event_id": "EVT-WEB-001",
        "event_type": "validated_success",
        "contributor": "agent:web-test",
        "operator": "user:alice",
        "project": "knowledge-base",
        "scenario_id": "web-form-create",
        "evidence_group_id": "web-mvp-test-2026-07-11",
        "validation_method": "integration_test",
        "result_summary": "通过网页 API 创建知识并生成 Catalog",
        "reference": "tests/test_web_api.py",
    }
    response = client.post(f"/api/knowledge/{knowledge_id}/events", json=event)
    assert response.status_code == 200, response.text
    assert response.json()["created"] is True
    evidence = (web_repo / "evidence" / f"{knowledge_id}.yaml").read_text(encoding="utf-8")
    assert "EVT-WEB-001" in evidence
    candidates = client.get("/api/lifecycle/candidates").json()["items"]
    assert any(item["knowledge_id"] == knowledge_id and item["proposals"][0]["to"] == "verified" for item in candidates)
    options = client.get(f"/api/knowledge/{knowledge_id}/transition-options").json()
    assert options["current"] == {"maturity": "draft", "status": "active"}
    assert options["proposals"][0]["to"] == "verified"
    proposal = client.post(f"/api/knowledge/{knowledge_id}/transition-proposal", headers={"X-User": "alice"})
    assert proposal.status_code == 200, proposal.text
    proposal_path = web_repo / proposal.json()["path"]
    assert proposal_path.exists()
    assert "proposed_by: alice" in proposal_path.read_text(encoding="utf-8")


def test_validation_event_requires_independence_fields(client):
    client.post("/api/knowledge", json=guideline_payload())
    response = client.post("/api/knowledge/TK-GDL-001/events", json={"event_type": "validated_success"})
    assert response.status_code == 422
    assert "evidence_group_id" in response.text


def test_domain_rejects_path_traversal(client):
    payload = guideline_payload()
    payload["domain"] = "../../outside"
    response = client.post("/api/knowledge", json=payload)
    assert response.status_code == 422
    assert not response.is_success


def test_duplicate_id_and_direct_reclassification_are_rejected(client):
    payload = guideline_payload()
    payload["id"] = "TK-GDL-009"
    assert client.post("/api/knowledge", json=payload).status_code == 200
    duplicate = client.post("/api/knowledge", json=payload)
    assert duplicate.status_code == 409
    changed = guideline_payload()
    changed["id"] = "TK-GDL-009"
    changed["scope"] = "biz"
    response = client.put("/api/knowledge/TK-GDL-009", json=changed)
    assert response.status_code == 409
    assert "scope" in response.json()["message"]
