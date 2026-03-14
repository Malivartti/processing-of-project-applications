import io
from unittest.mock import AsyncMock, patch

import openpyxl
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.schemas.excel_import import ImportPreviewResponse, ImportRowError


def make_xlsx_bytes(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "Название",
            "Описание проблемы",
            "Цель",
            "Ожидаемый результат",
            "Текущий",
            "Направление",
            "Приоритетное направление",
            "УГТ",
        ]
    )
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_template_download(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/projects/template")
        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]
        assert "projects_template.xlsx" in response.headers["content-disposition"]
        # xlsx magic bytes PK\x03\x04
        assert response.content[:4] == b"PK\x03\x04"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_import_preview_valid(mock_db):
    xlsx_bytes = make_xlsx_bytes(
        [["Проект 1", "Проблема", "Цель", "Результат", "Нет", None, None, None]]
    )
    preview = ImportPreviewResponse(valid_count=1, error_count=0, errors=[], duplicates=[])

    with patch("app.api.projects.ExcelImportService") as MockService:
        MockService.return_value.parse_and_validate = AsyncMock(return_value=([], preview))
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects/import",
                    files={
                        "file": (
                            "test.xlsx",
                            xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            assert response.status_code == 200
            data = response.json()
            assert data["valid_count"] == 1
            assert data["error_count"] == 0
            assert data["errors"] == []
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_import_preview_errors(mock_db):
    xlsx_bytes = make_xlsx_bytes([["", None, None, None, None, None, None, None]])
    error = ImportRowError(row=2, field="Название", message="Обязательное поле")
    preview = ImportPreviewResponse(valid_count=0, error_count=1, errors=[error], duplicates=[])

    with patch("app.api.projects.ExcelImportService") as MockService:
        MockService.return_value.parse_and_validate = AsyncMock(return_value=([], preview))
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects/import",
                    files={
                        "file": (
                            "test.xlsx",
                            xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            assert response.status_code == 200
            data = response.json()
            assert data["error_count"] == 1
            assert len(data["errors"]) == 1
            assert data["errors"][0]["field"] == "Название"
            assert data["errors"][0]["row"] == 2
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_import_confirm(mock_db):
    xlsx_bytes = make_xlsx_bytes(
        [["Проект 1", "Проблема", "Цель", "Результат", "Нет", None, None, None]]
    )
    fake_row = object()
    preview = ImportPreviewResponse(valid_count=1, error_count=0, errors=[], duplicates=[])

    with patch("app.api.projects.ExcelImportService") as MockService:
        MockService.return_value.parse_and_validate = AsyncMock(
            return_value=([fake_row], preview)
        )
        MockService.return_value.do_import = AsyncMock(return_value=1)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects/import?confirm=true",
                    files={
                        "file": (
                            "test.xlsx",
                            xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            assert response.status_code == 200
            data = response.json()
            assert data["valid_count"] == 1
            MockService.return_value.do_import.assert_called_once_with([fake_row])
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_import_duplicate_warning(mock_db):
    xlsx_bytes = make_xlsx_bytes([["Дубликат", None, None, None, "Нет", None, None, None]])
    preview = ImportPreviewResponse(
        valid_count=1, error_count=0, errors=[], duplicates=["Дубликат"]
    )

    with patch("app.api.projects.ExcelImportService") as MockService:
        MockService.return_value.parse_and_validate = AsyncMock(return_value=([], preview))
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects/import",
                    files={
                        "file": (
                            "test.xlsx",
                            xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            assert response.status_code == 200
            data = response.json()
            assert "Дубликат" in data["duplicates"]
        finally:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_import_confirm_no_valid_rows(mock_db):
    """confirm=true with zero valid rows imports nothing."""
    xlsx_bytes = make_xlsx_bytes([])
    preview = ImportPreviewResponse(valid_count=0, error_count=0, errors=[], duplicates=[])

    with patch("app.api.projects.ExcelImportService") as MockService:
        MockService.return_value.parse_and_validate = AsyncMock(return_value=([], preview))
        MockService.return_value.do_import = AsyncMock(return_value=0)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/projects/import?confirm=true",
                    files={
                        "file": (
                            "test.xlsx",
                            xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            assert response.status_code == 200
            assert response.json()["valid_count"] == 0
        finally:
            app.dependency_overrides.pop(get_db, None)
