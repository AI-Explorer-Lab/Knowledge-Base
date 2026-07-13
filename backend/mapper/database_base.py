from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Base


ModelT = TypeVar("ModelT", bound=Base)


class AsyncCrudMapper(Generic[ModelT]):
    """Minimal reusable async CRUD mapper for operational database entities."""

    def __init__(self, model: Type[ModelT]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, primary_key: Any) -> Optional[ModelT]:
        return await session.get(self.model, primary_key)

    async def list(self, session: AsyncSession, *, limit: int = 100) -> List[ModelT]:
        result = await session.scalars(select(self.model).limit(limit))
        return list(result)

    async def create(self, session: AsyncSession, values: Dict[str, Any]) -> ModelT:
        entity = self.model(**values)
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return entity

    async def update(
        self,
        session: AsyncSession,
        primary_key: Any,
        values: Dict[str, Any],
    ) -> Optional[ModelT]:
        primary_key_column = list(self.model.__table__.primary_key.columns)[0]
        await session.execute(
            update(self.model).where(primary_key_column == primary_key).values(**values)
        )
        await session.flush()
        return await self.get(session, primary_key)

    async def delete(self, session: AsyncSession, primary_key: Any) -> bool:
        primary_key_column = list(self.model.__table__.primary_key.columns)[0]
        result = await session.execute(
            delete(self.model).where(primary_key_column == primary_key)
        )
        await session.flush()
        return bool(result.rowcount)
