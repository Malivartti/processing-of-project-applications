import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Direction, PriorityDirection, TRLLevel
from app.schemas.dictionary import DictionaryItemCreate, DictionaryItemRead, DictionaryItemUpdate
from app.services.dictionary import DictionaryService

router = APIRouter(prefix="/api/dictionaries", tags=["dictionaries"])

DICT_TYPE_MAP = {
    "directions": Direction,
    "priority_directions": PriorityDirection,
    "trl_levels": TRLLevel,
}


def resolve_model(dict_type: str) -> type:
    model = DICT_TYPE_MAP.get(dict_type)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Unknown dictionary type: {dict_type}")
    return model


@router.get("/{dict_type}", response_model=list[DictionaryItemRead])
async def get_all(
    dict_type: str,
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list:
    model = resolve_model(dict_type)
    service = DictionaryService(db, model)
    return await service.get_all(active_only=active_only)


@router.post("/{dict_type}", response_model=DictionaryItemRead, status_code=201)
async def create(
    dict_type: str,
    body: DictionaryItemCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    model = resolve_model(dict_type)
    service = DictionaryService(db, model)
    return await service.create(name=body.name, level=body.level)


@router.patch("/{dict_type}/{item_id}", response_model=DictionaryItemRead)
async def update(
    dict_type: str,
    item_id: uuid.UUID,
    body: DictionaryItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    model = resolve_model(dict_type)
    service = DictionaryService(db, model)
    return await service.update(item_id, name=body.name, level=body.level)


@router.delete("/{dict_type}/{item_id}", status_code=204)
async def deactivate(
    dict_type: str,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    model = resolve_model(dict_type)
    service = DictionaryService(db, model)
    await service.deactivate(item_id)
