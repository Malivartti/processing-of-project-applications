import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Project
from app.repositories.project import ProjectFilters, ProjectRepo
from app.schemas.project import (
    GroupInfo,
    ProjectCreate,
    ProjectListItem,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
    StatsCounters,
)


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ProjectRepo(session)

    def _to_list_item(self, project: Project) -> ProjectListItem:
        return ProjectListItem(
            id=project.id,
            title=project.title,
            is_ongoing=project.is_ongoing,
            is_selected=project.is_selected,
            is_auto_checked=project.is_auto_checked,
            source=project.source,
            direction_id=project.direction_id,
            direction_name=project.direction.name if project.direction else None,
            priority_direction_id=project.priority_direction_id,
            trl_id=project.trl_id,
            group_id=project.group_id,
            group_name=project.group.name if project.group else None,
            group_source=project.group.source if project.group else None,
            created_at=project.created_at,
        )

    def _to_read(self, project: Project) -> ProjectRead:
        group_info = None
        if project.group:
            group_info = GroupInfo(
                id=project.group.id,
                name=project.group.name,
                source=project.group.source,
                context=project.group.context,
                is_confirmed=project.group.is_confirmed,
            )
        return ProjectRead(
            id=project.id,
            title=project.title,
            problem=project.problem,
            goal=project.goal,
            expected_result=project.expected_result,
            is_ongoing=project.is_ongoing,
            is_selected=project.is_selected,
            is_auto_checked=project.is_auto_checked,
            source=project.source,
            direction_id=project.direction_id,
            direction_name=project.direction.name if project.direction else None,
            priority_direction_id=project.priority_direction_id,
            priority_direction_name=(
                project.priority_direction.name if project.priority_direction else None
            ),
            trl_id=project.trl_id,
            trl_name=project.trl_level.name if project.trl_level else None,
            group=group_info,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def get_list(
        self,
        filters: ProjectFilters,
        limit: int = 20,
        offset: int = 0,
    ) -> ProjectListResponse:
        items, total = await self.repo.get_list(filters, limit=limit, offset=offset)
        return ProjectListResponse(
            items=[self._to_list_item(p) for p in items],
            total=total,
        )

    async def get_by_id(self, project_id: uuid.UUID) -> ProjectRead:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError(detail=f"Project {project_id} not found")
        return self._to_read(project)

    async def create(self, body: ProjectCreate) -> ProjectRead:
        data = body.model_dump(exclude_none=False)
        project = await self.repo.create(data)
        return self._to_read(project)

    async def update(self, project_id: uuid.UUID, body: ProjectUpdate) -> ProjectRead:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        project = await self.repo.update(project_id, data)
        if project is None:
            raise NotFoundError(detail=f"Project {project_id} not found")
        return self._to_read(project)

    async def delete(self, project_id: uuid.UUID) -> None:
        deleted = await self.repo.delete(project_id)
        if not deleted:
            raise NotFoundError(detail=f"Project {project_id} not found")

    async def set_selected(self, project_id: uuid.UUID, is_selected: bool) -> ProjectRead:
        project = await self.repo.set_selected(project_id, is_selected)
        if project is None:
            raise NotFoundError(detail=f"Project {project_id} not found")
        return self._to_read(project)

    async def get_stats(self) -> StatsCounters:
        stats = await self.repo.count_stats()
        return StatsCounters(**stats)
