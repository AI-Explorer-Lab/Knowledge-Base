from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from .errors import KnowledgeError


def normalize(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def load_yaml(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return normalize(yaml.safe_load(handle))
    except yaml.YAMLError as exc:
        raise KnowledgeError(f"{path}: YAML 解析失败：{exc}") from exc


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000)


def load_front_matter(path: Path) -> Tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise KnowledgeError(f"{path}: 缺少 YAML Front Matter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise KnowledgeError(f"{path}: Front Matter 未闭合")
    raw = text[4:marker]
    try:
        metadata = normalize(yaml.safe_load(raw))
    except yaml.YAMLError as exc:
        raise KnowledgeError(f"{path}: Front Matter 解析失败：{exc}") from exc
    if not isinstance(metadata, dict):
        raise KnowledgeError(f"{path}: Front Matter 必须是对象")
    return metadata, text[marker + 5 :]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
