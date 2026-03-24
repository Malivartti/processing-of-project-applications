from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models import GroupContext, RunStatus


class GroupingRunCreate(BaseModel):
    threshold: float
    context: GroupContext = GroupContext.main


class GroupingRunRead(BaseModel):
    id: uuid.UUID
    status: RunStatus
    threshold: float
    context: GroupContext
    started_at: datetime
    finished_at: datetime | None = None
    projects_processed: int | None = None
    groups_found: int | None = None
    projects_in_groups: int | None = None
    error_message: str | None = None
    confirmed_rate: float | None = None

    model_config = {"from_attributes": True}


class GroupingStatusResponse(BaseModel):
    run_id: str
    stage: str | None = None
    current: int | None = None
    total: int | None = None
    status: str | None = None
    error_message: str | None = None
    groups_found: int | None = None


class GroupingRunStartRequest(BaseModel):
    threshold: float = Field(default=0.75, ge=0.5, le=0.95)
    context: str = "main"


class GroupingRunStartResponse(BaseModel):
    run_id: str


class GroupingHistoryResponse(BaseModel):
    items: list[GroupingRunRead]
    total: int
