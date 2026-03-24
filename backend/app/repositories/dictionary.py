from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError
from app.models import Direction, PriorityDirection, Stopword, TRLLevel

T = TypeVar("T", Direction, PriorityDirection, TRLLevel, Stopword)


class DictionaryRepo(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self.session = session
        self.model = model

    async def get_all(self, active_only: bool = False) -> list[T]:
        q = select(self.model)
        if active_only:
            q = q.where(self.model.is_active.is_(True))
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, item_id: UUID) -> T | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == item_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: object) -> T:
        item = self.model(**kwargs)
        self.session.add(item)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(detail="Такое значение уже существует")
        await self.session.refresh(item)
        return item

    async def update(self, item_id: UUID, data: dict) -> T | None:
        item = await self.get_by_id(item_id)
        if item is None:
            return None
        for key, value in data.items():
            setattr(item, key, value)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def deactivate(self, item_id: UUID) -> T | None:
        item = await self.get_by_id(item_id)
        if item is None:
            return None
        item.is_active = False
        await self.session.commit()
        await self.session.refresh(item)
        return item
