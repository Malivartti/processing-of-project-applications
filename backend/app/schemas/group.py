import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models import GroupContext, GroupSource


class GroupProjectItem(BaseModel):
    id: uuid.UUID
    title: str

    model_config = {"from_attributes": True}


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    source: GroupSource
    context: GroupContext
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
    projects: list[GroupProjectItem]

    model_config = {"from_attributes": True}


class GroupListItem(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    source: GroupSource
    context: GroupContext
    is_confirmed: bool
    project_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    project_ids: list[uuid.UUID]
    context: GroupContext = GroupContext.main

    @field_validator("project_ids")
    @classmethod
    def min_two_projects(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(v) < 2:
            raise ValueError("At least 2 projects are required")
        return v


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupListResponse(BaseModel):
    items: list[GroupListItem]
    total: int


class AddProjectToGroup(BaseModel):
    project_id: uuid.UUID


class ConflictingProject(BaseModel):
    project_id: uuid.UUID
    group_id: uuid.UUID
    group_name: str
