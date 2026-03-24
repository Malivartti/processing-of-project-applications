import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DictionaryItemCreate(BaseModel):
    name: str
    level: int | None = None  # Only used for trl_levels


class DictionaryItemUpdate(BaseModel):
    name: str | None = None
    level: int | None = None  # Only used for trl_levels
    is_active: bool | None = None


class DictionaryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    level: int | None = None  # Only present for trl_levels
