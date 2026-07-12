from pathlib import Path

from knowledge_governance.catalog import build_catalogs
from knowledge_governance.repository import Repository
from knowledge_governance.validator import validate


ROOT = Path(__file__).resolve().parents[1]


def test_repository_examples_pass_lint():
    repo = Repository(ROOT)
    findings = validate(ROOT, repo.load_knowledge(), repo.load_evidence())
    assert [item.render() for item in findings if item.severity == "error"] == []
    profiles = repo.load_project_profiles()
    assert profiles["knowledge-base"]["project"]["knowledge_path"] == "docs/knowledge"


def test_catalog_generation_is_deterministic():
    repo = Repository(ROOT)
    records = repo.load_knowledge()
    evidence = repo.load_evidence()
    policy = repo.policy("review")
    build_catalogs(ROOT, records, evidence, policy)
    first = (ROOT / "knowledge-catalog.md").read_bytes()
    build_catalogs(ROOT, records, evidence, policy)
    second = (ROOT / "knowledge-catalog.md").read_bytes()
    assert first == second
    tech_catalog = (ROOT / "tech-wiki" / "catalog.md").read_text(encoding="utf-8")
    assert "(guidelines/TK-GDL-001.md)" in tech_catalog
    team_catalog = (ROOT / "team-conventions" / "catalog.md").read_text(encoding="utf-8")
    assert "TM-GDL-001" in team_catalog
    project_catalog = (ROOT / "docs" / "knowledge" / "catalog.md").read_text(encoding="utf-8")
    assert "PK-DEC-001" in project_catalog
