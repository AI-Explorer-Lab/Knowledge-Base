from __future__ import annotations

from typing import Any

from sqlalchemy import text

from backend.database import session as database_session
from backend.database.models import Base


async def create_tables() -> None:
    if database_session.async_engine is None:
        raise RuntimeError("database has not been configured")
    async with database_session.async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def init_database(settings: Any = None) -> None:
    if settings is None:
        from backend.config.config import settings as default_settings

        settings = default_settings
    database_session.configure_database(
        str(settings.database_url),
        echo=bool(settings.database_echo),
    )
    if bool(settings.database_create_tables):
        await create_tables()


async def close_database() -> None:
    if database_session.async_engine is not None:
        await database_session.async_engine.dispose()
    database_session.async_engine = None
    database_session.async_session_factory = None


async def database_is_ready() -> bool:
    if database_session.async_engine is None:
        return False
    try:
        async with database_session.async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
