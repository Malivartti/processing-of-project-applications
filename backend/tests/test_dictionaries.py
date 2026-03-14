import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


def make_direction(name: str = "Test Direction", is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
    )


def make_trl(name: str = "ТРЛ 1", level: int = 1, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        level=level,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_all_directions(mock_db):
    items = [make_direction("Dir A"), make_direction("Dir B")]
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.get_all = AsyncMock(return_value=items)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/dictionaries/directions")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Dir A"
            assert data[0]["level"] is None
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_all_active_only(mock_db):
    active = make_direction("Active")
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.get_all = AsyncMock(return_value=[active])
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/dictionaries/directions?active_only=true")
            assert response.status_code == 200
            MockService.return_value.get_all.assert_called_once_with(active_only=True)
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_trl_levels_includes_level_field(mock_db):
    items = [make_trl("ТРЛ 1", level=1), make_trl("ТРЛ 2", level=2)]
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.get_all = AsyncMock(return_value=items)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/dictionaries/trl_levels")
            assert response.status_code == 200
            data = response.json()
            assert data[0]["level"] == 1
            assert data[1]["level"] == 2
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_direction(mock_db):
    created = make_direction("New Direction")
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.create = AsyncMock(return_value=created)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/dictionaries/directions", json={"name": "New Direction"}
                )
            assert response.status_code == 201
            assert response.json()["name"] == "New Direction"
            MockService.return_value.create.assert_called_once_with(
                name="New Direction", level=None
            )
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_trl_level_with_level(mock_db):
    created = make_trl("ТРЛ 3", level=3)
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.create = AsyncMock(return_value=created)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/dictionaries/trl_levels", json={"name": "ТРЛ 3", "level": 3}
                )
            assert response.status_code == 201
            assert response.json()["level"] == 3
            MockService.return_value.create.assert_called_once_with(name="ТРЛ 3", level=3)
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_update_direction(mock_db):
    item_id = uuid.uuid4()
    updated = make_direction("Updated Direction")
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.update = AsyncMock(return_value=updated)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.patch(
                    f"/api/dictionaries/directions/{item_id}",
                    json={"name": "Updated Direction"},
                )
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Direction"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_update_not_found(mock_db):
    from app.exceptions import NotFoundError

    item_id = uuid.uuid4()
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.update = AsyncMock(
            side_effect=NotFoundError(detail="Item not found")
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.patch(
                    f"/api/dictionaries/directions/{item_id}", json={"name": "X"}
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_deactivate_direction(mock_db):
    item_id = uuid.uuid4()
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.deactivate = AsyncMock(return_value=None)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(f"/api/dictionaries/directions/{item_id}")
            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_deactivate_not_found(mock_db):
    from app.exceptions import NotFoundError

    item_id = uuid.uuid4()
    with patch("app.api.dictionaries.DictionaryService") as MockService:
        MockService.return_value.deactivate = AsyncMock(
            side_effect=NotFoundError(detail="Item not found")
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(f"/api/dictionaries/directions/{item_id}")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_unknown_dict_type(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/dictionaries/unknown_type")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
