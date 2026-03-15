import uuid

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Group, GroupSource, Project


class ProjectFilters:
    def __init__(
        self,
        direction_id: uuid.UUID | None = None,
        priority_direction_id: uuid.UUID | None = None,
        trl_id: uuid.UUID | None = None,
        is_ongoing: bool | None = None,
        has_group: bool | None = None,
        group_source: GroupSource | None = None,
        search: str | None = None,
        is_selected: bool | None = None,
    ) -> None:
        self.direction_id = direction_id
        self.priority_direction_id = priority_direction_id
        self.trl_id = trl_id
        self.is_ongoing = is_ongoing
        self.has_group = has_group
        self.group_source = group_source
        self.search = search
        self.is_selected = is_selected


class ProjectRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _apply_filters(self, q: sa.Select, filters: ProjectFilters) -> sa.Select:
        if filters.direction_id is not None:
            q = q.where(Project.direction_id == filters.direction_id)
        if filters.priority_direction_id is not None:
            q = q.where(Project.priority_direction_id == filters.priority_direction_id)
        if filters.trl_id is not None:
            q = q.where(Project.trl_id == filters.trl_id)
        if filters.is_ongoing is not None:
            q = q.where(Project.is_ongoing == filters.is_ongoing)
        if filters.group_source is not None:
            q = q.join(Group, Project.group_id == Group.id).where(
                Group.source == filters.group_source
            )
        elif filters.has_group is not None:
            if filters.has_group:
                q = q.where(Project.group_id.is_not(None))
            else:
                q = q.where(Project.group_id.is_(None))
        if filters.is_selected is not None:
            q = q.where(Project.is_selected == filters.is_selected)
        if filters.search:
            q = q.where(
                sa.text(
                    "to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(problem,'') || ' '"
                    " || coalesce(goal,'') || ' ' || coalesce(expected_result,'')) @@ "
                    "plainto_tsquery('russian', :search)"
                ).bindparams(search=filters.search)
            )
        return q

    async def get_list(
        self,
        filters: ProjectFilters,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Project], int]:
        count_q = select(func.count(Project.id))
        count_q = self._apply_filters(count_q, filters)
        total = (await self.session.execute(count_q)).scalar_one()

        list_q = (
            select(Project)
            .options(
                selectinload(Project.direction),
                selectinload(Project.priority_direction),
                selectinload(Project.trl_level),
                selectinload(Project.group),
            )
        )
        list_q = self._apply_filters(list_q, filters)
        list_q = list_q.order_by(Project.created_at.desc()).limit(limit).offset(offset)
        items = list((await self.session.execute(list_q)).scalars().unique().all())

        return items, total

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.direction),
                selectinload(Project.priority_direction),
                selectinload(Project.trl_level),
                selectinload(Project.group),
            )
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Project:
        project = Project(**data)
        self.session.add(project)
        await self.session.commit()
        result = await self.get_by_id(project.id)
        assert result is not None
        return result

    async def update(self, project_id: uuid.UUID, data: dict) -> Project | None:
        project = await self.session.get(Project, project_id)
        if project is None:
            return None
        for key, value in data.items():
            setattr(project, key, value)
        await self.session.commit()
        return await self.get_by_id(project_id)

    async def delete(self, project_id: uuid.UUID) -> bool:
        project = await self.session.get(Project, project_id)
        if project is None:
            return False
        await self.session.delete(project)
        await self.session.commit()
        return True

    async def set_selected(self, project_id: uuid.UUID, is_selected: bool) -> Project | None:
        return await self.update(project_id, {"is_selected": is_selected})

    async def count_stats(self) -> dict:
        total = (await self.session.execute(select(func.count(Project.id)))).scalar_one()
        new = (
            await self.session.execute(
                select(func.count(Project.id)).where(Project.is_auto_checked.is_(False))
            )
        ).scalar_one()
        auto_checked = (
            await self.session.execute(
                select(func.count(Project.id)).where(Project.is_auto_checked.is_(True))
            )
        ).scalar_one()
        return {"total": total, "new": new, "auto_checked": auto_checked}
