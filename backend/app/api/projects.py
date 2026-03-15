import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GroupSource
from app.repositories.project import ProjectFilters
from app.schemas.compare import CompareResponse
from app.schemas.excel_import import ImportPreviewResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
    StatsCounters,
)
from app.services.compare import CompareService
from app.services.excel_export import ExcelExportService, ExportContext
from app.services.excel_import import ExcelImportService, build_template_xlsx
from app.services.project import ProjectService

router = APIRouter(tags=["projects"])


@router.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    direction_id: uuid.UUID | None = Query(None),
    priority_direction_id: uuid.UUID | None = Query(None),
    trl_id: uuid.UUID | None = Query(None),
    is_ongoing: bool | None = Query(None),
    has_group: bool | None = Query(None),
    group_source: GroupSource | None = Query(None),
    search: str | None = Query(None),
    is_selected: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    filters = ProjectFilters(
        direction_id=direction_id,
        priority_direction_id=priority_direction_id,
        trl_id=trl_id,
        is_ongoing=is_ongoing,
        has_group=has_group,
        group_source=group_source,
        search=search,
        is_selected=is_selected,
    )
    service = ProjectService(db)
    return await service.get_list(filters, limit=limit, offset=offset)


@router.get("/api/projects/export")
async def export_projects(
    context: ExportContext = Query("all"),
    direction_id: uuid.UUID | None = Query(None),
    priority_direction_id: uuid.UUID | None = Query(None),
    trl_id: uuid.UUID | None = Query(None),
    is_ongoing: bool | None = Query(None),
    has_group: bool | None = Query(None),
    group_source: GroupSource | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = ExcelExportService(db)
    filtered_projects = None
    if context == "filtered":
        filters = ProjectFilters(
            direction_id=direction_id,
            priority_direction_id=priority_direction_id,
            trl_id=trl_id,
            is_ongoing=is_ongoing,
            has_group=has_group,
            group_source=group_source,
            search=search,
        )
        from app.repositories.project import ProjectRepo

        repo = ProjectRepo(db)
        filtered_projects, _ = await repo.get_list(filters, limit=10000, offset=0)
    xlsx_bytes = await service.export(context=context, filtered_projects=filtered_projects)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=projects_export.xlsx"},
    )


@router.get("/api/projects/template")
async def download_template() -> Response:
    xlsx_bytes = build_template_xlsx()
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=projects_template.xlsx"},
    )


MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/api/projects/import", response_model=ImportPreviewResponse)
async def import_projects(
    file: UploadFile = File(...),
    confirm: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    from fastapi import HTTPException

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB")
    service = ExcelImportService(db)
    valid_rows, preview = await service.parse_and_validate(file_bytes)
    if confirm:
        imported = await service.do_import(valid_rows)
        return ImportPreviewResponse(
            valid_count=imported,
            error_count=preview.error_count,
            errors=preview.errors,
            duplicates=preview.duplicates,
        )
    return preview


@router.get("/api/projects/compare", response_model=CompareResponse)
async def compare_projects(
    a: uuid.UUID = Query(...),
    b: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    service = CompareService(db)
    return await service.compare(a, b)


@router.get("/api/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.get_by_id(project_id)


@router.post("/api/projects", response_model=ProjectRead, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.create(body)


@router.patch("/api/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.update(project_id, body)


@router.delete("/api/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ProjectService(db)
    await service.delete(project_id)


@router.post("/api/projects/{project_id}/select", response_model=ProjectRead)
async def select_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.set_selected(project_id, is_selected=True)


@router.delete("/api/projects/{project_id}/select", response_model=ProjectRead)
async def deselect_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.set_selected(project_id, is_selected=False)


@router.get("/api/stats/counters", response_model=StatsCounters)
async def stats_counters(
    db: AsyncSession = Depends(get_db),
) -> StatsCounters:
    service = ProjectService(db)
    return await service.get_stats()
