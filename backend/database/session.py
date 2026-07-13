from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


async_engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def configure_database(database_url: str, *, echo: bool = False) -> AsyncEngine:
    global async_engine, async_session_factory
    async_engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return async_engine


async def get_session() -> AsyncIterator[AsyncSession]:
    if async_session_factory is None:
        raise RuntimeError("database has not been initialised")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
