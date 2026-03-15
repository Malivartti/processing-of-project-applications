from __future__ import annotations

import uuid

import redis.asyncio as aioredis
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.exceptions import ConflictError, NotFoundError
from app.limiter import limiter
from app.models import GroupContext, GroupingRun, RunStatus
from app.schemas.grouping import (
    GroupingHistoryResponse,
    GroupingRunRead,
    GroupingRunStartRequest,
    GroupingRunStartResponse,
    GroupingStatusResponse,
)
from app.tasks.grouping import run_grouping_task

router = APIRouter(prefix="/api/grouping", tags=["grouping"])

LOCK_TTL = 3600  # seconds


async def _get_redis() -> aioredis.Redis:
    return aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.post("/run", response_model=GroupingRunStartResponse, status_code=201)
@limiter.limit("1/30 seconds")
async def start_grouping(
    request: Request,
    body: GroupingRunStartRequest,
    db: AsyncSession = Depends(get_db),
) -> GroupingRunStartResponse:
    """Start auto-grouping. Returns run_id. Returns 409 if already running."""
    r = await _get_redis()
    try:
        lock_key = f"grouping:lock:{body.context}"

        # Check Redis lock
        already_locked = await r.exists(lock_key)
        if already_locked:
            raise ConflictError(detail="Auto-grouping is already running for this context")

        # Validate context
        try:
            ctx = GroupContext(body.context)
        except ValueError:
            from app.exceptions import ValidationError

            raise ValidationError(detail=f"Invalid context: {body.context}")

        # Create GroupingRun record with status='pending'
        run_id = uuid.uuid4()
        grouping_run = GroupingRun(
            id=run_id,
            threshold=body.threshold,
            context=ctx,
            status=RunStatus.pending,
        )
        db.add(grouping_run)
        await db.commit()

        # Set Redis lock
        await r.set(lock_key, str(run_id), ex=LOCK_TTL)

        # Write initial progress so status polling doesn't get 404 before the task starts
        progress_key = f"grouping:progress:{run_id}"
        await r.hset(
            progress_key,
            mapping={"stage": "pending", "current": "0", "total": "0", "status": "pending"},
        )
        await r.expire(progress_key, LOCK_TTL)

        # Launch Celery task
        run_grouping_task.delay(str(run_id), body.threshold, body.context)

        return GroupingRunStartResponse(run_id=str(run_id))
    finally:
        await r.aclose()


@router.get("/status/{run_id}", response_model=GroupingStatusResponse)
async def get_grouping_status(run_id: str) -> GroupingStatusResponse:
    """Get auto-grouping progress from Redis."""
    r = await _get_redis()
    try:
        progress_key = f"grouping:progress:{run_id}"
        data = await r.hgetall(progress_key)

        if not data:
            raise NotFoundError(detail=f"No status found for run_id={run_id}")

        return GroupingStatusResponse(
            run_id=run_id,
            stage=data.get("stage"),
            current=int(data["current"]) if data.get("current") is not None else None,
            total=int(data["total"]) if data.get("total") is not None else None,
            status=data.get("status"),
            error_message=data.get("error_message"),
        )
    finally:
        await r.aclose()


@router.get("/history", response_model=GroupingHistoryResponse)
async def get_grouping_history(
    db: AsyncSession = Depends(get_db),
) -> GroupingHistoryResponse:
    """Return history of grouping runs ordered by started_at desc."""
    from app.models import Group, GroupSource

    result = await db.execute(
        sa.select(GroupingRun).order_by(GroupingRun.started_at.desc())
    )
    runs = list(result.scalars().all())

    # Compute confirmed_rate per context: confirmed auto-groups / total auto-groups
    rate_result = await db.execute(
        sa.select(
            Group.context,
            sa.func.count(Group.id).label("total"),
            sa.func.sum(sa.cast(Group.is_confirmed, sa.Integer)).label("confirmed"),
        )
        .where(Group.source == GroupSource.auto)
        .group_by(Group.context)
    )
    rates: dict[str, float | None] = {}
    for row in rate_result:
        total = row.total or 0
        confirmed = row.confirmed or 0
        rates[row.context.value] = (confirmed / total) if total > 0 else 0.0

    items = []
    for run in runs:
        run_data = GroupingRunRead.model_validate(run)
        run_data.confirmed_rate = rates.get(run.context.value)
        items.append(run_data)

    return GroupingHistoryResponse(items=items, total=len(items))
