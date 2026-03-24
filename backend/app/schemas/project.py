import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models import GroupContext, GroupSource, ProjectSource


class DirectionInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class PriorityDirectionInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class TRLLevelInfo(BaseModel):
    id: uuid.UUID
    name: str
    level: int

    model_config = {"from_attributes": True}


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
    participants_count: int
    group_id: uuid.UUID | None
    group_name: str | None
    group_source: GroupSource | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: uuid.UUID
    title: str
    direction: DirectionInfo | None
    is_ongoing: bool
    priority_direction: PriorityDirectionInfo | None
    implementation_period: int
    relevance: str
    problem: str
    goal: str
    key_tasks: str
    expected_result: str
    trl_level: TRLLevelInfo | None
    budget: int
    support_master_classes: bool
    support_consultations: bool
    support_equipment: bool
    support_product_samples: bool
    support_materials: bool
    support_software_licenses: bool
    support_project_site: bool
    support_internship: bool
    non_financial_support: str | None
    participants_count: int
    is_selected: bool
    is_auto_checked: bool
    source: ProjectSource
    group: GroupInfo | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=80)
    direction_id: uuid.UUID
    is_ongoing: bool = False
    priority_direction_id: uuid.UUID | None = None
    implementation_period: int = Field(..., ge=1)
    relevance: str = Field(..., max_length=1500)
    problem: str = Field(..., max_length=1500)
    goal: str = Field(..., max_length=1000)
    key_tasks: str = Field(..., max_length=1500)
    expected_result: str = Field(..., max_length=1000)
    trl_id: uuid.UUID
    budget: int = Field(..., ge=0)
    support_master_classes: bool = False
    support_consultations: bool = False
    support_equipment: bool = False
    support_product_samples: bool = False
    support_materials: bool = False
    support_software_licenses: bool = False
    support_project_site: bool = False
    support_internship: bool = False
    non_financial_support: str | None = Field(default=None, max_length=3000)
    participants_count: int = Field(..., ge=1)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    direction_id: uuid.UUID | None = None
    is_ongoing: bool | None = None
    priority_direction_id: uuid.UUID | None = None
    implementation_period: int | None = Field(default=None, ge=1)
    relevance: str | None = Field(default=None, max_length=1500)
    problem: str | None = Field(default=None, max_length=1500)
    goal: str | None = Field(default=None, max_length=1000)
    key_tasks: str | None = Field(default=None, max_length=1500)
    expected_result: str | None = Field(default=None, max_length=1000)
    trl_id: uuid.UUID | None = None
    budget: int | None = Field(default=None, ge=0)
    support_master_classes: bool | None = None
    support_consultations: bool | None = None
    support_equipment: bool | None = None
    support_product_samples: bool | None = None
    support_materials: bool | None = None
    support_software_licenses: bool | None = None
    support_project_site: bool | None = None
    support_internship: bool | None = None
    non_financial_support: str | None = Field(default=None, max_length=3000)
    participants_count: int | None = Field(default=None, ge=1)


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]
    total: int


class StatsCounters(BaseModel):
    total: int
    new: int
    auto_checked: int
