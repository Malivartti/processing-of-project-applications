import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GroupSource
from app.repositories.project import ProjectFilters
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
    StatsCounters,
)
from app.services.project import ProjectService

router = APIRouter(tags=["projects"])


@router.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    direction_id: uuid.UUID | None = Query(None),
    priority_direction_id: uuid.UUID | None = Query(None),
    trl_id: uuid.UUID | None = Query(None),
    is_ongoing: bool | None = Query(None),
    has_group: bool | None = Query(None),
    group_source: GroupSource | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    filters = ProjectFilters(
        direction_id=direction_id,
        priority_direction_id=priority_direction_id,
        trl_id=trl_id,
        is_ongoing=is_ongoing,
        has_group=has_group,
        group_source=group_source,
        search=search,
    )
    service = ProjectService(db)
    return await service.get_list(filters, limit=limit, offset=offset)


@router.get("/api/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.get_by_id(project_id)


@router.post("/api/projects", response_model=ProjectRead, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.create(body)


@router.patch("/api/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.update(project_id, body)


@router.delete("/api/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ProjectService(db)
    await service.delete(project_id)


@router.post("/api/projects/{project_id}/select", response_model=ProjectRead)
async def select_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.set_selected(project_id, is_selected=True)


@router.delete("/api/projects/{project_id}/select", response_model=ProjectRead)
async def deselect_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.set_selected(project_id, is_selected=False)


@router.get("/api/stats/counters", response_model=StatsCounters)
async def stats_counters(
    db: AsyncSession = Depends(get_db),
) -> StatsCounters:
    service = ProjectService(db)
    return await service.get_stats()
