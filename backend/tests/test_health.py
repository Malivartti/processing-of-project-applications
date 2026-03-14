from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


async def mock_get_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    yield session


@pytest.mark.asyncio
async def test_health():
    app.dependency_overrides[get_db] = mock_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "ok"
    finally:
        app.dependency_overrides.clear()
