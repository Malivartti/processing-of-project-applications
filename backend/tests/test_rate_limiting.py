from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app

# ---------------------------------------------------------------------------
# File size limit (50 MB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_import_file_too_large():
    """POST /api/projects/import should return 413 if file exceeds 50 MB."""
    mock_db = AsyncMock()
    large_file = io.BytesIO(b"x" * (50 * 1024 * 1024 + 1))

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/projects/import",
                files={"file": ("big.xlsx", large_file, "application/octet-stream")},
            )
        assert response.status_code == 413
        assert "50 MB" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Rate limit on POST /api/grouping/run (1/10 seconds)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_grouping_run_rate_limit_returns_429():
    """POST /api/grouping/run should return 429 when called twice within 10s."""
    mock_db = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    mock_task = MagicMock()
    mock_task.delay = MagicMock()

    with (
        patch("app.api.grouping._get_redis", return_value=mock_redis),
        patch("app.api.grouping.run_grouping_task", mock_task),
    ):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                r1 = await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
                r2 = await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
            assert r1.status_code == 201
            assert r2.status_code == 429
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_rate_limit_response_has_retry_after_header():
    """429 response from slowapi should include Retry-After header."""
    mock_db = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    mock_task = MagicMock()
    mock_task.delay = MagicMock()

    with (
        patch("app.api.grouping._get_redis", return_value=mock_redis),
        patch("app.api.grouping.run_grouping_task", mock_task),
    ):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
                r2 = await client.post(
                    "/api/grouping/run",
                    json={"threshold": 0.75, "context": "main"},
                )
            assert r2.status_code == 429
            assert "retry-after" in r2.headers
        finally:
            app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Infrastructure check
# ---------------------------------------------------------------------------


def test_limiter_attached_to_app():
    """The rate limiter should be attached to app.state."""
    from app.limiter import limiter

    assert app.state.limiter is limiter
