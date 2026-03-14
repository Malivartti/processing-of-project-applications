import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import GroupContext, GroupSource, ProjectSource
from app.schemas.project import (
    GroupInfo,
    ProjectListResponse,
    ProjectRead,
    StatsCounters,
)


def make_project_read(
    title: str = "Test Project",
    group: GroupInfo | None = None,
    is_selected: bool = False,
) -> ProjectRead:
    return ProjectRead(
        id=uuid.uuid4(),
        title=title,
        problem="Problem text",
        goal="Goal text",
        expected_result="Result text",
        is_ongoing=False,
        is_selected=is_selected,
        is_auto_checked=False,
        source=ProjectSource.manual,
        direction_id=None,
        direction_name=None,
        priority_direction_id=None,
        priority_direction_name=None,
        trl_id=None,
        trl_name=None,
        group=group,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_list_response(count: int = 2) -> ProjectListResponse:
    from app.schemas.project import ProjectListItem

    items = [
        ProjectListItem(
            id=uuid.uuid4(),
            title=f"Project {i}",
            is_ongoing=False,
            is_selected=False,
            is_auto_checked=False,
            source=ProjectSource.manual,
            direction_id=None,
            direction_name=None,
            priority_direction_id=None,
            trl_id=None,
            group_id=None,
            group_name=None,
            group_source=None,
            created_at=datetime.now(timezone.utc),
        )
        for i in range(count)
    ]
    return ProjectListResponse(items=items, total=count)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_projects(mock_db):
    response_data = make_list_response(3)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_list = AsyncMock(return_value=response_data)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/projects")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert len(data["items"]) == 3
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_projects_with_filters(mock_db):
    response_data = make_list_response(1)
    direction_id = uuid.uuid4()
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_list = AsyncMock(return_value=response_data)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/projects?direction_id={direction_id}&is_ongoing=false&limit=10&offset=0"
                )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_projects_search(mock_db):
    response_data = make_list_response(1)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_list = AsyncMock(return_value=response_data)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/projects?search=тест")
            assert response.status_code == 200
            MockService.return_value.get_list.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_project(mock_db):
    project = make_project_read("My Project")
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_by_id = AsyncMock(return_value=project)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/api/projects/{project.id}")
            assert response.status_code == 200
            assert response.json()["title"] == "My Project"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_project_not_found(mock_db):
    from app.exceptions import NotFoundError

    project_id = uuid.uuid4()
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_by_id = AsyncMock(
            side_effect=NotFoundError(detail="Project not found")
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/api/projects/{project_id}")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_project(mock_db):
    project = make_project_read("New Project")
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.create = AsyncMock(return_value=project)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects", json={"title": "New Project", "is_ongoing": False}
                )
            assert response.status_code == 201
            assert response.json()["title"] == "New Project"
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_select_project(mock_db):
    project = make_project_read("Selected", is_selected=True)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.set_selected = AsyncMock(return_value=project)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(f"/api/projects/{project.id}/select")
            assert response.status_code == 200
            assert response.json()["is_selected"] is True
            MockService.return_value.set_selected.assert_called_once_with(
                project.id, is_selected=True
            )
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_deselect_project(mock_db):
    project = make_project_read("Deselected", is_selected=False)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.set_selected = AsyncMock(return_value=project)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(f"/api/projects/{project.id}/select")
            assert response.status_code == 200
            assert response.json()["is_selected"] is False
            MockService.return_value.set_selected.assert_called_once_with(
                project.id, is_selected=False
            )
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_delete_project(mock_db):
    project_id = uuid.uuid4()
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.delete = AsyncMock(return_value=None)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete(f"/api/projects/{project_id}")
            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_stats_counters(mock_db):
    stats = StatsCounters(total=100, new=30, auto_checked=70)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_stats = AsyncMock(return_value=stats)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/stats/counters")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 100
            assert data["new"] == 30
            assert data["auto_checked"] == 70
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_project_with_group(mock_db):
    group = GroupInfo(
        id=uuid.uuid4(),
        name="Group A",
        source=GroupSource.auto,
        context=GroupContext.main,
        is_confirmed=False,
    )
    project = make_project_read("Project with group", group=group)
    with patch("app.api.projects.ProjectService") as MockService:
        MockService.return_value.get_by_id = AsyncMock(return_value=project)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/api/projects/{project.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["group"]["name"] == "Group A"
            assert data["group"]["source"] == "auto"
            assert data["group"]["is_confirmed"] is False
        finally:
            app.dependency_overrides.pop(get_db, None)
