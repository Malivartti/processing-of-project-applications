from __future__ import annotations

import uuid
from datetime import datetime, timezone

import redis
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GroupingRun, RunStatus
from app.services.clustering import run_auto_grouping
from app.tasks.celery_app import celery


def _get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


def _get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


LOCK_TTL = 3600  # seconds
PROGRESS_TTL = 3600  # seconds


@celery.task(name="app.tasks.grouping.run_grouping_task")
def run_grouping_task(run_id: str, threshold: float, context: str) -> dict:
    """Celery task to run auto-grouping pipeline with progress tracking via Redis."""
    r = _get_redis()
    progress_key = f"grouping:progress:{run_id}"
    lock_key = f"grouping:lock:{context}"

    def update_progress(stage: str, current: int, total: int) -> None:
        r.hset(
            progress_key,
            mapping={"stage": stage, "current": str(current), "total": str(total)},
        )

    with _get_sync_session() as session:
        # Update grouping run status to running
        grouping_run: GroupingRun | None = session.execute(
            sa.select(GroupingRun).where(GroupingRun.id == uuid.UUID(run_id))
        ).scalar_one_or_none()

        if grouping_run is None:
            r.hset(
                progress_key,
                mapping={"stage": "failed", "current": "0", "total": "0", "status": "failed",
                         "error_message": "GroupingRun record not found"},
            )
            r.expire(progress_key, PROGRESS_TTL)
            return {"error": "GroupingRun not found"}

        grouping_run.status = RunStatus.running
        session.commit()

        # Update initial progress
        r.hset(
            progress_key,
            mapping={"stage": "embeddings", "current": "0", "total": "0", "status": "running"},
        )

        try:
            result = run_auto_grouping(
                session=session,
                threshold=threshold,
                context=context,
                grouping_run_id=uuid.UUID(run_id),
                progress_callback=update_progress,
            )

            # Mark completed
            grouping_run.status = RunStatus.completed
            grouping_run.finished_at = datetime.now(timezone.utc)
            grouping_run.projects_processed = result["projects_processed"]
            grouping_run.groups_found = result["groups_found"]
            grouping_run.projects_in_groups = result["projects_in_groups"]
            session.commit()

            r.hset(
                progress_key,
                mapping={
                    "stage": "done",
                    "current": str(result["projects_processed"]),
                    "total": str(result["projects_processed"]),
                    "status": "completed",
                },
            )
            r.expire(progress_key, PROGRESS_TTL)

            return result

        except Exception as exc:
            error_msg = str(exc)
            try:
                grouping_run.status = RunStatus.failed
                grouping_run.finished_at = datetime.now(timezone.utc)
                grouping_run.error_message = error_msg
                session.commit()
            except Exception:
                session.rollback()

            r.hset(
                progress_key,
                mapping={
                    "stage": "failed",
                    "current": "0",
                    "total": "0",
                    "status": "failed",
                    "error_message": error_msg,
                },
            )
            r.expire(progress_key, PROGRESS_TTL)
            raise

        finally:
            # Release the lock
            r.delete(lock_key)
