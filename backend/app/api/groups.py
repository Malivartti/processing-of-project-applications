import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GroupContext, GroupSource
from app.schemas.group import (
    AddProjectToGroup,
    GroupCreate,
    GroupListResponse,
    GroupRead,
    GroupUpdate,
)
from app.services.group import GroupService

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("", response_model=GroupListResponse)
async def list_groups(
    source: GroupSource | None = None,
    context: GroupContext | None = None,
    is_confirmed: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> GroupListResponse:
    svc = GroupService(db)
    return await svc.get_all(
        source=source,
        context=context.value if context else None,
        is_confirmed=is_confirmed,
    )


@router.post("", response_model=GroupRead, status_code=201)
async def create_group(
    body: GroupCreate,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.create_group(body)


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.get_by_id(group_id)


@router.patch("/{group_id}", response_model=GroupRead)
async def update_group(
    group_id: uuid.UUID,
    body: GroupUpdate,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.update_group(group_id, body)


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = GroupService(db)
    await svc.delete_group(group_id)


@router.post("/{group_id}/confirm", response_model=GroupRead)
async def confirm_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.confirm_group(group_id)


@router.post("/{group_id}/projects", response_model=GroupRead)
async def add_project_to_group(
    group_id: uuid.UUID,
    body: AddProjectToGroup,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.add_project(group_id, body)


@router.delete("/{group_id}/projects/{project_id}", response_model=GroupRead)
async def remove_project_from_group(
    group_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GroupRead:
    svc = GroupService(db)
    return await svc.remove_project(group_id, project_id)
