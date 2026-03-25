import itertools
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Group, GroupContext, GroupSource, Project, RejectedPair


class GroupFilters:
    def __init__(
        self,
        source: GroupSource | None = None,
        context: GroupContext | None = None,
        is_confirmed: bool | None = None,
    ) -> None:
        self.source = source
        self.context = context
        self.is_confirmed = is_confirmed


class GroupRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, filters: GroupFilters) -> tuple[list[Group], int]:
        count_q = select(func.count(Group.id))
        list_q = select(Group).options(selectinload(Group.projects))

        if filters.source is not None:
            count_q = count_q.where(Group.source == filters.source)
            list_q = list_q.where(Group.source == filters.source)
        if filters.context is not None:
            count_q = count_q.where(Group.context == filters.context)
            list_q = list_q.where(Group.context == filters.context)
        if filters.is_confirmed is not None:
            count_q = count_q.where(Group.is_confirmed == filters.is_confirmed)
            list_q = list_q.where(Group.is_confirmed == filters.is_confirmed)

        total = (await self.session.execute(count_q)).scalar_one()
        list_q = list_q.order_by(Group.created_at.desc())
        items = list((await self.session.execute(list_q)).scalars().unique().all())
        return items, total

    async def get_by_id(self, group_id: uuid.UUID) -> Group | None:
        result = await self.session.execute(
            select(Group)
            .options(selectinload(Group.projects))
            .where(Group.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_projects_by_ids(self, project_ids: list[uuid.UUID]) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.group))
            .where(Project.id.in_(project_ids))
        )
        return list(result.scalars().all())

    async def create(self, data: dict, project_ids: list[uuid.UUID]) -> Group:
        group = Group(**data)
        self.session.add(group)
        await self.session.flush()  # get group.id without committing

        # Assign projects to this group
        await self.session.execute(
            update(Project)
            .where(Project.id.in_(project_ids))
            .values(group_id=group.id)
        )
        await self.session.commit()

        result = await self.get_by_id(group.id)
        assert result is not None
        return result

    async def update(self, group_id: uuid.UUID, data: dict) -> Group | None:
        group = await self.session.get(Group, group_id)
        if group is None:
            return None
        for key, value in data.items():
            setattr(group, key, value)
        await self.session.commit()
        return await self.get_by_id(group_id)

    async def delete(self, group_id: uuid.UUID) -> bool:
        group = await self.session.get(Group, group_id)
        if group is None:
            return False
        # Nullify group_id on all projects
        await self.session.execute(
            update(Project).where(Project.group_id == group_id).values(group_id=None)
        )
        await self.session.delete(group)
        await self.session.commit()
        return True

    async def confirm(self, group_id: uuid.UUID) -> Group | None:
        return await self.update(group_id, {"is_confirmed": True})

    async def add_project(self, group_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Assign project to group. Returns False if project not found."""
        project = await self.session.get(Project, project_id)
        if project is None:
            return False
        project.group_id = group_id
        await self.session.commit()
        return True

    async def remove_project(self, group_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Remove project from group. Returns False if project not found or not in this group."""
        project = await self.session.get(Project, project_id)
        if project is None or project.group_id != group_id:
            return False
        project.group_id = None
        await self.session.commit()
        return True

    async def save_rejected_pairs_for_removal(
        self, removed_project_id: uuid.UUID, group_project_ids: list[uuid.UUID]
    ) -> None:
        """Save rejected pairs: removed project vs all remaining projects in the group."""
        pairs = [
            RejectedPair(project_a_id=removed_project_id, project_b_id=other_id)
            for other_id in group_project_ids
            if other_id != removed_project_id
        ]
        if pairs:
            self.session.add_all(pairs)
            # no commit here — caller commits after remove_project

    async def delete_all_by_source(self, source: GroupSource, context: GroupContext | None = None) -> int:
        """Delete all groups with given source. Returns count deleted."""
        from sqlalchemy import delete as sa_delete

        q = select(Group.id).where(Group.source == source, Group.is_confirmed == False)  # noqa: E712
        if context is not None:
            q = q.where(Group.context == context)
        ids = list((await self.session.execute(q)).scalars().all())
        if not ids:
            return 0
        await self.session.execute(
            update(Project).where(Project.group_id.in_(ids)).values(group_id=None)
        )
        await self.session.execute(sa_delete(Group).where(Group.id.in_(ids)))
        await self.session.commit()
        return len(ids)

    async def save_rejected_pairs_for_group(self, project_ids: list[uuid.UUID]) -> None:
        """Save rejected pairs for all pairs within a group being deleted."""
        pairs = [
            RejectedPair(project_a_id=a, project_b_id=b)
            for a, b in itertools.combinations(project_ids, 2)
        ]
        if pairs:
            self.session.add_all(pairs)
            # no commit here — caller commits after delete
