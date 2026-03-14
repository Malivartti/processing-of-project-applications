import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import GroupContext, GroupSource, ProjectSource


class GroupInfo(BaseModel):
    id: uuid.UUID
    name: str
    source: GroupSource
    context: GroupContext
    is_confirmed: bool

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    id: uuid.UUID
    title: str
    is_ongoing: bool
    is_selected: bool
    is_auto_checked: bool
    source: ProjectSource
    direction_id: uuid.UUID | None
    direction_name: str | None
    priority_direction_id: uuid.UUID | None
    trl_id: uuid.UUID | None
    group_id: uuid.UUID | None
    group_name: str | None
    group_source: GroupSource | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: uuid.UUID
    title: str
    problem: str | None
    goal: str | None
    expected_result: str | None
    is_ongoing: bool
    is_selected: bool
    is_auto_checked: bool
    source: ProjectSource
    direction_id: uuid.UUID | None
    direction_name: str | None
    priority_direction_id: uuid.UUID | None
    priority_direction_name: str | None
    trl_id: uuid.UUID | None
    trl_name: str | None
    group: GroupInfo | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    title: str
    problem: str | None = None
    goal: str | None = None
    expected_result: str | None = None
    is_ongoing: bool = False
    direction_id: uuid.UUID | None = None
    priority_direction_id: uuid.UUID | None = None
    trl_id: uuid.UUID | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    problem: str | None = None
    goal: str | None = None
    expected_result: str | None = None
    is_ongoing: bool | None = None
    direction_id: uuid.UUID | None = None
    priority_direction_id: uuid.UUID | None = None
    trl_id: uuid.UUID | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]
    total: int


class StatsCounters(BaseModel):
    total: int
    new: int
    auto_checked: int
