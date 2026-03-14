import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models import Group, GroupSource
from app.repositories.group import GroupFilters, GroupRepo
from app.schemas.group import (
    AddProjectToGroup,
    ConflictingProject,
    GroupCreate,
    GroupListItem,
    GroupListResponse,
    GroupProjectItem,
    GroupRead,
    GroupUpdate,
)


class GroupService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = GroupRepo(session)

    def _to_read(self, group: Group) -> GroupRead:
        return GroupRead(
            id=group.id,
            name=group.name,
            description=group.description,
            source=group.source,
            context=group.context,
            is_confirmed=group.is_confirmed,
            created_at=group.created_at,
            updated_at=group.updated_at,
            projects=[GroupProjectItem(id=p.id, title=p.title) for p in group.projects],
        )

    def _to_list_item(self, group: Group) -> GroupListItem:
        return GroupListItem(
            id=group.id,
            name=group.name,
            description=group.description,
            source=group.source,
            context=group.context,
            is_confirmed=group.is_confirmed,
            project_count=len(group.projects),
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async def get_all(
        self,
        source: GroupSource | None = None,
        context: str | None = None,
        is_confirmed: bool | None = None,
    ) -> GroupListResponse:
        from app.models import GroupContext

        ctx = GroupContext(context) if context else None
        filters = GroupFilters(source=source, context=ctx, is_confirmed=is_confirmed)
        items, total = await self.repo.get_all(filters)
        return GroupListResponse(
            items=[self._to_list_item(g) for g in items],
            total=total,
        )

    async def get_by_id(self, group_id: uuid.UUID) -> GroupRead:
        group = await self.repo.get_by_id(group_id)
        if group is None:
            raise NotFoundError(detail=f"Group {group_id} not found")
        return self._to_read(group)

    async def create_group(self, body: GroupCreate) -> GroupRead:
        project_ids = list(dict.fromkeys(body.project_ids))  # deduplicate, preserve order

        # Check for conflicts: projects already in another group
        projects = await self.repo.get_projects_by_ids(project_ids)
        found_ids = {p.id for p in projects}
        missing = [pid for pid in project_ids if pid not in found_ids]
        if missing:
            raise NotFoundError(detail=f"Projects not found: {missing}")

        conflicting = [
            ConflictingProject(
                project_id=p.id,
                group_id=p.group_id,  # type: ignore[arg-type]
                group_name=p.group.name if p.group else "",
            )
            for p in projects
            if p.group_id is not None
        ]
        if conflicting:
            raise ConflictError(
                detail={
                    "message": "Some projects are already in a group",
                    "conflicting": [c.model_dump(mode="json") for c in conflicting],
                }
            )

        data = {
            "name": body.name,
            "description": body.description,
            "source": GroupSource.manual,
            "context": body.context,
        }
        group = await self.repo.create(data, project_ids)
        return self._to_read(group)

    async def update_group(self, group_id: uuid.UUID, body: GroupUpdate) -> GroupRead:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        group = await self.repo.update(group_id, data)
        if group is None:
            raise NotFoundError(detail=f"Group {group_id} not found")
        return self._to_read(group)

    async def delete_group(self, group_id: uuid.UUID) -> None:
        deleted = await self.repo.delete(group_id)
        if not deleted:
            raise NotFoundError(detail=f"Group {group_id} not found")

    async def confirm_group(self, group_id: uuid.UUID) -> GroupRead:
        group = await self.repo.confirm(group_id)
        if group is None:
            raise NotFoundError(detail=f"Group {group_id} not found")
        return self._to_read(group)

    async def add_project(self, group_id: uuid.UUID, body: AddProjectToGroup) -> GroupRead:
        group = await self.repo.get_by_id(group_id)
        if group is None:
            raise NotFoundError(detail=f"Group {group_id} not found")

        project = await self.repo.get_projects_by_ids([body.project_id])
        if not project:
            raise NotFoundError(detail=f"Project {body.project_id} not found")

        p = project[0]
        if p.group_id is not None and p.group_id != group_id:
            raise ConflictError(
                detail={
                    "message": "Project is already in another group",
                    "conflicting": [
                        ConflictingProject(
                            project_id=p.id,
                            group_id=p.group_id,
                            group_name=p.group.name if p.group else "",
                        ).model_dump(mode="json")
                    ],
                }
            )

        await self.repo.add_project(group_id, body.project_id)
        updated = await self.repo.get_by_id(group_id)
        assert updated is not None
        return self._to_read(updated)

    async def remove_project(self, group_id: uuid.UUID, project_id: uuid.UUID) -> GroupRead:
        group = await self.repo.get_by_id(group_id)
        if group is None:
            raise NotFoundError(detail=f"Group {group_id} not found")

        removed = await self.repo.remove_project(group_id, project_id)
        if not removed:
            raise NotFoundError(
                detail=f"Project {project_id} not found in group {group_id}"
            )

        updated = await self.repo.get_by_id(group_id)
        assert updated is not None
        return self._to_read(updated)
