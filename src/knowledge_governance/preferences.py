from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import KnowledgeError
from .yaml_io import atomic_write, dump_yaml, load_yaml


DEFAULT_PERSONAL_ROOT = Path.home() / ".ai-team"

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "version": 1,
    "communication": {
        "language": "zh-CN",
        "detail_level": "concise",
        "outcome_first": True,
    },
    "coding": {
        "preserve_existing_style": True,
        "comments_explain_why": True,
    },
    "workflow": {
        "inspect_before_editing": True,
        "run_relevant_tests": True,
        "auto_commit": False,
    },
    "tools": {
        "text_search": "rg",
        "python_tests": "pytest",
    },
}

DEFAULT_INSTRUCTIONS = """# 个人协作偏好

- 非阻塞的小问题可以自行做合理假设。
- 修改完成后说明改了什么以及测试结果。
- 不要未经确认自动提交或推送代码。
- 代码审查先关注错误、安全和回归风险。
"""


def _validate_preferences(path: Path, data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise KnowledgeError(f"{path}: 个人偏好必须是 YAML 对象")
    if data.get("version") != 1:
        raise KnowledgeError(f"{path}: 仅支持个人偏好版本 1")
    return data


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key == "version":
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def init_personal_preferences(personal_root: Optional[Path] = None) -> Dict[str, bool]:
    root = (personal_root or DEFAULT_PERSONAL_ROOT).expanduser().resolve()
    preferences_path = root / "preferences.yaml"
    instructions_path = root / "instructions.md"
    (root / "project-overrides").mkdir(parents=True, exist_ok=True)

    created = {"preferences": False, "instructions": False}
    if not preferences_path.exists():
        atomic_write(preferences_path, dump_yaml(DEFAULT_PREFERENCES))
        created["preferences"] = True
    if not instructions_path.exists():
        atomic_write(instructions_path, DEFAULT_INSTRUCTIONS)
        created["instructions"] = True
    return created


def load_personal_context(
    project_root: Optional[Path] = None,
    personal_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = (personal_root or DEFAULT_PERSONAL_ROOT).expanduser().resolve()
    project = (project_root or Path.cwd()).resolve()
    preferences_path = root / "preferences.yaml"
    instructions_path = root / "instructions.md"

    preferences: Dict[str, Any] = {}
    loaded_files = []
    if preferences_path.exists():
        preferences = _validate_preferences(preferences_path, load_yaml(preferences_path))
        loaded_files.append(str(preferences_path))

    override_path = root / "project-overrides" / f"{project.name}.yaml"
    if override_path.exists():
        override = _validate_preferences(override_path, load_yaml(override_path))
        preferences = _merge(preferences, override)
        loaded_files.append(str(override_path))

    instructions = ""
    if instructions_path.exists():
        instructions = instructions_path.read_text(encoding="utf-8").strip()
        loaded_files.append(str(instructions_path))

    return {
        "personal_root": str(root),
        "project_root": str(project),
        "preferences": preferences,
        "instructions": instructions,
        "loaded_files": loaded_files,
    }
