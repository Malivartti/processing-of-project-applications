import io
import uuid
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Project, SimilarityScore

ExportContext = Literal["all", "filtered", "selected", "grouped"]

EXPORT_COLUMNS = [
    "Название",
    "Описание проблемы",
    "Цель",
    "Ожидаемый результат",
    "Текущий",
    "Направление",
    "Приоритетное направление",
    "УГТ",
    "В отборе",
    "Источник",
    "Группа",
    "Score",
]


class ExcelExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_group_avg_scores(
        self, group_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, float]:
        if not group_ids:
            return {}

        proj_a = Project.__table__.alias("proj_a")
        proj_b = Project.__table__.alias("proj_b")

        q = (
            select(
                proj_a.c.group_id,
                func.avg(SimilarityScore.score).label("avg_score"),
            )
            .join(proj_a, SimilarityScore.project_a_id == proj_a.c.id)
            .join(proj_b, SimilarityScore.project_b_id == proj_b.c.id)
            .where(proj_a.c.group_id.in_(group_ids))
            .where(proj_a.c.group_id == proj_b.c.group_id)
            .group_by(proj_a.c.group_id)
        )

        result = await self.session.execute(q)
        return {row.group_id: round(float(row.avg_score), 3) for row in result.fetchall()}

    async def _fetch_all_projects(self) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.direction),
                selectinload(Project.priority_direction),
                selectinload(Project.trl_level),
                selectinload(Project.group),
            )
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def _fetch_selected_projects(self) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.direction),
                selectinload(Project.priority_direction),
                selectinload(Project.trl_level),
                selectinload(Project.group),
            )
            .where(Project.is_selected.is_(True))
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def _fetch_grouped_projects(self) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.direction),
                selectinload(Project.priority_direction),
                selectinload(Project.trl_level),
                selectinload(Project.group),
            )
            .where(Project.group_id.is_not(None))
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def export(
        self,
        context: ExportContext,
        filtered_projects: list[Project] | None = None,
    ) -> bytes:
        if context == "all":
            projects = await self._fetch_all_projects()
        elif context == "filtered":
            projects = filtered_projects or await self._fetch_all_projects()
        elif context == "selected":
            projects = await self._fetch_selected_projects()
        elif context == "grouped":
            projects = await self._fetch_grouped_projects()
        else:
            projects = await self._fetch_all_projects()

        group_ids = [p.group_id for p in projects if p.group_id is not None]
        avg_scores = await self._get_group_avg_scores(list(set(group_ids)))

        return self._build_xlsx(projects, avg_scores)

    def _build_xlsx(
        self, projects: list[Project], avg_scores: dict[uuid.UUID, float]
    ) -> bytes:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Проекты"
        ws.append(EXPORT_COLUMNS)

        for p in projects:
            group_name = p.group.name if p.group else None
            score = avg_scores.get(p.group_id) if p.group_id else None
            ws.append(
                [
                    p.title,
                    p.problem,
                    p.goal,
                    p.expected_result,
                    "Да" if p.is_ongoing else "Нет",
                    p.direction.name if p.direction else None,
                    p.priority_direction.name if p.priority_direction else None,
                    p.trl_level.name if p.trl_level else None,
                    "Да" if p.is_selected else "Нет",
                    p.source.value,
                    group_name,
                    score,
                ]
            )

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
