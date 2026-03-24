from typing import Type
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.repositories.dictionary import DictionaryRepo


class DictionaryService:
    def __init__(self, session: AsyncSession, model: Type) -> None:
        self.repo: DictionaryRepo = DictionaryRepo(session, model)
        self.model = model

    async def get_all(self, active_only: bool = False) -> list:
        return await self.repo.get_all(active_only=active_only)

    async def create(self, name: str, level: int | None = None) -> object:
        kwargs: dict = {"name": name}
        if level is not None and hasattr(self.model, "level"):
            kwargs["level"] = level
        return await self.repo.create(**kwargs)

    async def update(self, item_id: UUID, name: str | None, level: int | None, is_active: bool | None = None) -> object:
        data: dict = {}
        if name is not None:
            data["name"] = name
        if level is not None and hasattr(self.model, "level"):
            data["level"] = level
        if is_active is not None:
            data["is_active"] = is_active
        item = await self.repo.update(item_id, data)
        if item is None:
            raise NotFoundError(detail=f"Item {item_id} not found")
        return item

    async def delete(self, item_id: UUID) -> None:
        found = await self.repo.delete(item_id)
        if not found:
            raise NotFoundError(detail=f"Item {item_id} not found")
