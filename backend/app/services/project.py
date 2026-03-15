import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Project
from app.repositories.project import ProjectFilters, ProjectRepo
from app.schemas.project import (
    DirectionInfo,
    GroupInfo,
    PriorityDirectionInfo,
    ProjectCreate,
    ProjectListItem,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
    StatsCounters,
    TRLLevelInfo,
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
            direction_name=project.direction.name,
            priority_direction_id=project.priority_direction_id,
            trl_id=project.trl_id,
            participants_count=project.participants_count,
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
        priority_direction_info = None
        if project.priority_direction:
            priority_direction_info = PriorityDirectionInfo(
                id=project.priority_direction.id,
                name=project.priority_direction.name,
            )
        return ProjectRead(
            id=project.id,
            title=project.title,
            direction=DirectionInfo(id=project.direction.id, name=project.direction.name),
            is_ongoing=project.is_ongoing,
            priority_direction=priority_direction_info,
            implementation_period=project.implementation_period,
            relevance=project.relevance,
            problem=project.problem,
            goal=project.goal,
            key_tasks=project.key_tasks,
            expected_result=project.expected_result,
            trl_level=TRLLevelInfo(
                id=project.trl_level.id,
                name=project.trl_level.name,
                level=project.trl_level.level,
            ),
            budget=project.budget,
            support_master_classes=project.support_master_classes,
            support_consultations=project.support_consultations,
            support_equipment=project.support_equipment,
            support_product_samples=project.support_product_samples,
            support_materials=project.support_materials,
            support_software_licenses=project.support_software_licenses,
            support_project_site=project.support_project_site,
            support_internship=project.support_internship,
            non_financial_support=project.non_financial_support,
            participants_count=project.participants_count,
            is_selected=project.is_selected,
            is_auto_checked=project.is_auto_checked,
            source=project.source,
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
