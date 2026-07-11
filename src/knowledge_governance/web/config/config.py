from __future__ import annotations

from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf

from ...errors import KnowledgeError


SETTINGS_FILE = Path(__file__).with_name("app.yaml")


def load_settings(environment: Optional[str] = None) -> Dynaconf:
    return Dynaconf(
        settings_files=[str(SETTINGS_FILE)],
        environments=True,
        env=environment or "development",
        envvar_prefix="KNOWLEDGE",
        env_switcher="KNOWLEDGE_ENV",
        merge_enabled=True,
    )


def validate_settings(settings: Dynaconf) -> None:
    if not settings.get("web.host"):
        raise KnowledgeError("缺少 web.host 配置")
    port = settings.get("web.port")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise KnowledgeError("web.port 必须是 1 到 65535 的整数")
    if settings.get("db.enabled", False):
        raise KnowledgeError("当前版本以 Git 文件为事实来源，不支持启用数据库")
