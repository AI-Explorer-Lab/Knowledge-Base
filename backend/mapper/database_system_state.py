from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import SystemState
from backend.mapper.database_base import AsyncCrudMapper


system_state_mapper = AsyncCrudMapper(SystemState)


async def create(session: AsyncSession, values: Dict[str, Any]) -> SystemState:
    return await system_state_mapper.create(session, values)


async def get(session: AsyncSession, key: str) -> Optional[SystemState]:
    return await system_state_mapper.get(session, key)


async def list(session: AsyncSession, *, limit: int = 100) -> List[SystemState]:
    return await system_state_mapper.list(session, limit=limit)


async def update(
    session: AsyncSession,
    key: str,
    values: Dict[str, Any],
) -> Optional[SystemState]:
    return await system_state_mapper.update(session, key, values)


async def delete(session: AsyncSession, key: str) -> bool:
    return await system_state_mapper.delete(session, key)
