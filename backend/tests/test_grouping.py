from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import GroupContext, RunStatus
from app.schemas.grouping import GroupingRunRead
from app.services.clustering import run_auto_grouping


def make_run_read(
    status: RunStatus = RunStatus.completed,
    threshold: float = 0.75,
    context: GroupContext = GroupContext.main,
) -> GroupingRunRead:
    return GroupingRunRead(
        id=uuid.uuid4(),
        status=status,
        threshold=threshold,
        context=context,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        projects_processed=10,
        groups_found=2,
        projects_in_groups=6,
        error_message=None,
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


# ---------------------------------------------------------------------------
# POST /api/grouping/run
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_grouping_returns_run_id(mock_db):
    """POST /api/grouping/run should return a run_id."""
    run_id = str(uuid.uuid4())

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    mock_task = MagicMock()
    mock_task.delay = MagicMock()

    with (
        patch("app.api.grouping._get_redis", return_value=mock_redis),
        patch("app.api.grouping.run_grouping_task", mock_task),
        patch("app.api.grouping.uuid.uuid4", return_value=uuid.UUID(run_id)),
    ):  # noqa
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
            assert response.status_code == 201
            data = response.json()
            assert "run_id" in data
            assert data["run_id"] == run_id
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_start_grouping_conflict_when_lock_exists(mock_db):
    """POST /api/grouping/run should return 409 when lock exists."""
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # lock exists
    mock_redis.aclose = AsyncMock()

    with patch("app.api.grouping._get_redis", return_value=mock_redis):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
            assert response.status_code == 409
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_start_grouping_threshold_validation(mock_db):
    """POST /api/grouping/run should return 422 for out-of-range threshold."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/grouping/run",
                json={"threshold": 0.1, "context": "main"},
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# GET /api/grouping/status/{run_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_grouping_status_returns_progress():
    """GET /api/grouping/status/{run_id} should return progress from Redis."""
    run_id = str(uuid.uuid4())

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(
        return_value={
            "stage": "clustering",
            "current": "5",
            "total": "10",
            "status": "running",
        }
    )
    mock_redis.aclose = AsyncMock()

    with patch("app.api.grouping._get_redis", return_value=mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/grouping/status/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["stage"] == "clustering"
        assert data["current"] == 5
        assert data["total"] == 10
        assert data["status"] == "running"


@pytest.mark.asyncio
async def test_get_grouping_status_not_found():
    """GET /api/grouping/status/{run_id} should return 404 when no data in Redis."""
    run_id = str(uuid.uuid4())

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})
    mock_redis.aclose = AsyncMock()

    with patch("app.api.grouping._get_redis", return_value=mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/grouping/status/{run_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_grouping_status_completed():
    """GET /api/grouping/status/{run_id} returns completed state."""
    run_id = str(uuid.uuid4())

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(
        return_value={
            "stage": "done",
            "current": "100",
            "total": "100",
            "status": "completed",
        }
    )
    mock_redis.aclose = AsyncMock()

    with patch("app.api.grouping._get_redis", return_value=mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/grouping/status/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "done"
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# GET /api/grouping/history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_grouping_history_returns_list(mock_db):
    """GET /api/grouping/history should return list of runs."""
    runs = [make_run_read() for _ in range(3)]

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [
        MagicMock(
            id=r.id,
            status=r.status,
            threshold=r.threshold,
            context=r.context,
            started_at=r.started_at,
            finished_at=r.finished_at,
            projects_processed=r.projects_processed,
            groups_found=r.groups_found,
            projects_in_groups=r.projects_in_groups,
            error_message=r.error_message,
        )
        for r in runs
    ]

    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    mock_db.execute = AsyncMock(return_value=execute_result)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/grouping/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_grouping_history_empty(mock_db):
    """GET /api/grouping/history should return empty list when no runs."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []

    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    mock_db.execute = AsyncMock(return_value=execute_result)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/grouping/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# run_grouping_task (unit tests without actual Redis/DB/Celery)
# ---------------------------------------------------------------------------


def test_run_grouping_task_is_registered():
    """run_grouping_task should be registered in the Celery app."""
    import app.tasks.grouping  # noqa: F401 - ensure task module is imported
    from app.tasks.celery_app import celery

    assert "app.tasks.grouping.run_grouping_task" in celery.tasks


def test_progress_callback_in_clustering():
    """run_auto_grouping should call progress_callback at key stages."""
    # Build mock projects
    rng = np.random.default_rng(42)
    v = rng.standard_normal(312).astype(np.float32)
    v /= np.linalg.norm(v)

    def near_vec():
        noise = rng.standard_normal(312).astype(np.float32) * 0.001
        r = v + noise
        r /= np.linalg.norm(r)
        return r.tolist()

    mock_projects = []
    for _ in range(3):
        p = MagicMock()
        p.id = uuid.uuid4()
        p.embedding = near_vec()
        p.is_selected = False
        p.group_id = None
        mock_projects.append(p)

    call_count = [0]

    def execute_side_effect(stmt, *args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        c = call_count[0]
        call_count[0] += 1
        if c == 0:
            scalars.all.return_value = mock_projects
        elif c == 1:
            scalars.all.return_value = []  # no rejected pairs
        elif c == 2:
            scalars.all.return_value = []  # no old groups
        else:
            scalars.all.return_value = []
        result.scalars.return_value = scalars
        return result

    session = MagicMock()
    session.execute.side_effect = execute_side_effect

    callback_calls = []

    def callback(stage, current, total):
        callback_calls.append((stage, current, total))

    run_auto_grouping(session, threshold=0.75, context="main", progress_callback=callback)

    stages = [c[0] for c in callback_calls]
    assert "embeddings" in stages
    assert "similarity" in stages
    assert "clustering" in stages
