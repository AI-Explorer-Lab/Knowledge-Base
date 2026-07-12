from pathlib import Path

import pytest

from knowledge_governance.errors import KnowledgeError
from knowledge_governance.preferences import init_personal_preferences, load_personal_context


def test_missing_personal_preferences_are_optional(tmp_path: Path):
    context = load_personal_context(tmp_path / "project", tmp_path / "missing")

    assert context["preferences"] == {}
    assert context["instructions"] == ""
    assert context["loaded_files"] == []


def test_init_creates_minimal_files_without_overwriting(tmp_path: Path):
    personal_root = tmp_path / ".ai-team"

    first = init_personal_preferences(personal_root)
    original = personal_root / "preferences.yaml"
    original.write_text("version: 1\ncustom: keep-me\n", encoding="utf-8")
    second = init_personal_preferences(personal_root)

    assert first == {"preferences": True, "instructions": True}
    assert second == {"preferences": False, "instructions": False}
    assert "keep-me" in original.read_text(encoding="utf-8")
    assert (personal_root / "project-overrides").is_dir()


def test_project_override_is_merged(tmp_path: Path):
    personal_root = tmp_path / ".ai-team"
    init_personal_preferences(personal_root)
    project = tmp_path / "order-service"
    project.mkdir()
    (personal_root / "project-overrides" / "order-service.yaml").write_text(
        "version: 1\ncommunication:\n  detail_level: detailed\nworkflow:\n  auto_commit: true\n",
        encoding="utf-8",
    )

    context = load_personal_context(project, personal_root)

    assert context["preferences"]["communication"]["language"] == "zh-CN"
    assert context["preferences"]["communication"]["detail_level"] == "detailed"
    assert context["preferences"]["workflow"]["auto_commit"] is True


def test_invalid_version_is_rejected(tmp_path: Path):
    personal_root = tmp_path / ".ai-team"
    personal_root.mkdir()
    (personal_root / "preferences.yaml").write_text("version: 2\n", encoding="utf-8")

    with pytest.raises(KnowledgeError, match="仅支持个人偏好版本 1"):
        load_personal_context(tmp_path, personal_root)
