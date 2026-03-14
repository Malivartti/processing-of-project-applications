import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.exceptions import ConflictError, NotFoundError
from app.main import app
from app.models import GroupContext, GroupSource
from app.schemas.group import (
    GroupListItem,
    GroupListResponse,
    GroupProjectItem,
    GroupRead,
)


def make_group_read(
    name: str = "Test Group",
    source: GroupSource = GroupSource.manual,
    is_confirmed: bool = False,
    projects: list[GroupProjectItem] | None = None,
) -> GroupRead:
    return GroupRead(
        id=uuid.uuid4(),
        name=name,
        description=None,
        source=source,
        context=GroupContext.main,
        is_confirmed=is_confirmed,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        projects=projects or [],
    )


def make_list_response(count: int = 2) -> GroupListResponse:
    items = [
        GroupListItem(
            id=uuid.uuid4(),
            name=f"Group {i}",
            description=None,
            source=GroupSource.manual,
            context=GroupContext.main,
            is_confirmed=False,
            project_count=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(count)
    ]
    return GroupListResponse(items=items, total=count)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_groups(mock_db):
    response_data = make_list_response(3)
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.get_all = AsyncMock(return_value=response_data)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/groups")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert len(data["items"]) == 3
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_groups_with_filters(mock_db):
    response_data = make_list_response(1)
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.get_all = AsyncMock(return_value=response_data)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/groups?source=auto&is_confirmed=false")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_group(mock_db):
    group = make_group_read("New Group")
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.create_group = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/groups",
                    json={
                        "name": "New Group",
                        "project_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
                    },
                )
            assert response.status_code == 201
            assert response.json()["name"] == "New Group"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_group_requires_min_two_projects(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/groups",
                json={
                    "name": "Bad Group",
                    "project_ids": [str(uuid.uuid4())],
                },
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_group_conflict(mock_db):
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.create_group = AsyncMock(
            side_effect=ConflictError(detail={"message": "conflict", "conflicting": []})
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/groups",
                    json={
                        "name": "Conflict Group",
                        "project_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
                    },
                )
            assert response.status_code == 409
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_group(mock_db):
    group = make_group_read("My Group")
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.get_by_id = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/api/groups/{group.id}")
            assert response.status_code == 200
            assert response.json()["name"] == "My Group"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_update_group(mock_db):
    group = make_group_read("Updated Group")
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.update_group = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.patch(
                    f"/api/groups/{group.id}", json={"name": "Updated Group"}
                )
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Group"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_delete_group(mock_db):
    group_id = uuid.uuid4()
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.delete_group = AsyncMock(return_value=None)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(f"/api/groups/{group_id}")
            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_confirm_group(mock_db):
    group = make_group_read("Auto Group", source=GroupSource.auto, is_confirmed=True)
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.confirm_group = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(f"/api/groups/{group.id}/confirm")
            assert response.status_code == 200
            assert response.json()["is_confirmed"] is True
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_add_project_to_group(mock_db):
    project_id = uuid.uuid4()
    group = make_group_read(
        "Group",
        projects=[GroupProjectItem(id=project_id, title="Project")],
    )
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.add_project = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/groups/{group.id}/projects",
                    json={"project_id": str(project_id)},
                )
            assert response.status_code == 200
            assert len(response.json()["projects"]) == 1
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_remove_project_from_group(mock_db):
    project_id = uuid.uuid4()
    group = make_group_read("Group", projects=[])
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.remove_project = AsyncMock(return_value=group)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(
                    f"/api/groups/{group.id}/projects/{project_id}"
                )
            assert response.status_code == 200
            assert len(response.json()["projects"]) == 0
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_remove_project_not_found(mock_db):
    group_id = uuid.uuid4()
    project_id = uuid.uuid4()
    with patch("app.api.groups.GroupService") as MockService:
        MockService.return_value.remove_project = AsyncMock(
            side_effect=NotFoundError(detail="Project not found in group")
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(
                    f"/api/groups/{group_id}/projects/{project_id}"
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)
