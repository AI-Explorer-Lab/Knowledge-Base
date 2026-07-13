from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from dynaconf import Dynaconf


REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = Path(__file__).with_name("app.yaml")


def validate_settings(runtime: Dynaconf) -> Dynaconf:
    environment_section = runtime.get("environment", {})
    db_section = runtime.get("db", {})
    agent_section = runtime.get("agent", {})
    environment = str(
        runtime.get("environment_name")
        or environment_section.get("name", "development")
    ).lower()
    if environment not in {"development", "test", "production"}:
        raise ValueError("environment must be development, test, or production")
    runtime.set("environment_name", environment)

    repo_value = Path(str(runtime.get("repo_root") or agent_section.get("repo_root", REPO_ROOT)))
    repo_root = repo_value if repo_value.is_absolute() else REPO_ROOT / repo_value
    repo_root = repo_root.resolve()
    if not (repo_root / "knowledge-catalog.md").is_file():
        raise ValueError(f"repo_root is not a knowledge repository: {repo_root}")
    runtime.set("repo_root", repo_root)

    ttl = int(runtime.get("preview_ttl_seconds") or agent_section.get("preview_ttl_seconds", 300))
    if not 30 <= ttl <= 900:
        raise ValueError("preview_ttl_seconds must be between 30 and 900")
    runtime.set("preview_ttl_seconds", ttl)

    preview_secret = runtime.get("preview_secret") or agent_section.get("preview_secret", "")
    if isinstance(preview_secret, str):
        preview_secret_bytes = preview_secret.encode("utf-8")
    else:
        preview_secret_bytes = bytes(preview_secret)
    if environment == "production" and not preview_secret_bytes:
        raise ValueError(
            "production requires a stable KNOWLEDGE_AGENT__PREVIEW_SECRET"
        )
    if not preview_secret_bytes:
        preview_secret_bytes = secrets.token_bytes(32)
    if len(preview_secret_bytes) < 32:
        raise ValueError("preview_secret must contain at least 32 bytes")
    runtime.set("preview_secret", preview_secret_bytes)

    identity_secret = runtime.get("identity_hmac_secret") or agent_section.get(
        "identity_hmac_secret", ""
    )
    if isinstance(identity_secret, str):
        identity_secret_bytes = identity_secret.encode("utf-8")
    else:
        identity_secret_bytes = bytes(identity_secret)
    if environment == "production" and len(identity_secret_bytes) < 32:
        raise ValueError(
            "production requires KNOWLEDGE_AGENT__IDENTITY_HMAC_SECRET with 32 bytes"
        )
    runtime.set("identity_hmac_secret", identity_secret_bytes or None)

    origins = runtime.get("cors_origins") or environment_section.get("cors_origins", [])
    if isinstance(origins, str):
        origins = [item.strip() for item in origins.split(",") if item.strip()]
    origins = tuple(str(item) for item in origins)
    if environment == "production" and "*" in origins:
        raise ValueError("production cors_origins cannot contain '*'")
    runtime.set("cors_origins", origins)

    database_url = str(runtime.get("database_url") or db_section.get("url", "")).strip()
    if not database_url.startswith("sqlite+aiosqlite://"):
        raise ValueError("database_url must use the async sqlite+aiosqlite driver")
    relative_sqlite_prefix = "sqlite+aiosqlite:///"
    if database_url.startswith(relative_sqlite_prefix):
        sqlite_location = database_url[len(relative_sqlite_prefix) :]
        if sqlite_location != ":memory:" and not sqlite_location.startswith("/"):
            database_path = (repo_root / sqlite_location).resolve()
            database_url = f"{relative_sqlite_prefix}{database_path.as_posix()}"
    runtime.set("database_url", database_url)
    create_tables = runtime.get("database_create_tables")
    if create_tables is None:
        create_tables = db_section.get("create_tables", False)
    if not isinstance(create_tables, bool):
        raise ValueError("db.create_tables must be true or false")
    runtime.set("database_create_tables", create_tables)
    identity_max_skew_seconds = int(
        runtime.get("identity_max_skew_seconds")
        or agent_section.get("identity_max_skew_seconds", 60)
    )
    if not 5 <= identity_max_skew_seconds <= 300:
        raise ValueError("identity_max_skew_seconds must be between 5 and 300")
    runtime.set("identity_max_skew_seconds", identity_max_skew_seconds)
    runtime.set("dev_actor", str(runtime.get("dev_actor") or agent_section.get("dev_actor")))
    runtime.set("database_echo", bool(runtime.get("database_echo", db_section.get("echo", False))))
    runtime.set("log_level", str(runtime.get("log_level") or environment_section.get("log_level", "INFO")))
    return runtime


def load_environment(
    environment: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dynaconf:
    selected = environment or os.environ.get("KNOWLEDGE_ENV", "development")
    runtime = Dynaconf(
        envvar_prefix="KNOWLEDGE",
        settings_files=[str(SETTINGS_FILE)],
        environments=True,
        env=selected,
        load_dotenv=False,
        merge_enabled=True,
    )
    runtime.set("environment_name", selected)
    for key, value in (overrides or {}).items():
        runtime.set(key, value)
    return validate_settings(runtime)


settings = load_environment()
