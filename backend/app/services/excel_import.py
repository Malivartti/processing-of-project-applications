import io
import uuid
from dataclasses import dataclass

import openpyxl
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Direction, PriorityDirection, Project, ProjectSource, TRLLevel
from app.schemas.excel_import import ImportPreviewResponse, ImportRowError

TEMPLATE_COLUMNS = [
    "Название",
    "Описание проблемы",
    "Цель",
    "Ожидаемый результат",
    "Текущий",
    "Направление",
    "Приоритетное направление",
    "УГТ",
]

EXAMPLE_ROW = [
    "Пример проекта",
    "Описание проблемы проекта",
    "Цель проекта",
    "Ожидаемый результат",
    "Нет",
    "Информационные технологии",
    "Искусственный интеллект",
    "УГТ 3",
]


def build_template_xlsx() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Проекты"
    ws.append(TEMPLATE_COLUMNS)
    ws.append(EXAMPLE_ROW)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in ("да", "yes", "1", "true")


@dataclass
class ParsedRow:
    title: str
    problem: str | None
    goal: str | None
    expected_result: str | None
    is_ongoing: bool
    direction_id: uuid.UUID | None
    priority_direction_id: uuid.UUID | None
    trl_id: uuid.UUID | None


class ExcelImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._directions: dict[str, uuid.UUID] = {}
        self._priority_directions: dict[str, uuid.UUID] = {}
        self._trl_levels: dict[str, uuid.UUID] = {}

    async def _load_dicts(self) -> None:
        directions = (
            await self.session.execute(select(Direction).where(Direction.is_active.is_(True)))
        ).scalars().all()
        self._directions = {d.name.strip().lower(): d.id for d in directions}

        priority_dirs = (
            await self.session.execute(
                select(PriorityDirection).where(PriorityDirection.is_active.is_(True))
            )
        ).scalars().all()
        self._priority_directions = {p.name.strip().lower(): p.id for p in priority_dirs}

        trl_levels = (
            await self.session.execute(select(TRLLevel).where(TRLLevel.is_active.is_(True)))
        ).scalars().all()
        self._trl_levels = {t.name.strip().lower(): t.id for t in trl_levels}

    async def _get_existing_titles(self) -> set[str]:
        result = await self.session.execute(select(Project.title))
        return {row[0].strip().lower() for row in result.fetchall()}

    def _parse_file(self, file_bytes: bytes) -> list[dict]:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if not rows:
            return []

        header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        col_idx = {name: i for i, name in enumerate(header)}

        def get_cell(row: tuple, col_name: str) -> str | None:
            idx = col_idx.get(col_name)
            if idx is None or idx >= len(row):
                return None
            val = row[idx]
            if val is None:
                return None
            text = str(val).strip()
            return text if text else None

        data = []
        for row in rows[1:]:
            if all(cell is None for cell in row):
                continue
            data.append(
                {
                    "title": get_cell(row, "Название"),
                    "problem": get_cell(row, "Описание проблемы"),
                    "goal": get_cell(row, "Цель"),
                    "expected_result": get_cell(row, "Ожидаемый результат"),
                    "is_ongoing_raw": get_cell(row, "Текущий"),
                    "direction_name": get_cell(row, "Направление"),
                    "priority_direction_name": get_cell(row, "Приоритетное направление"),
                    "trl_name": get_cell(row, "УГТ"),
                }
            )
        return data

    async def parse_and_validate(
        self, file_bytes: bytes
    ) -> tuple[list[ParsedRow], ImportPreviewResponse]:
        await self._load_dicts()
        existing_titles = await self._get_existing_titles()

        raw_rows = self._parse_file(file_bytes)

        errors: list[ImportRowError] = []
        duplicates: list[str] = []
        valid_rows: list[ParsedRow] = []
        seen_titles: set[str] = set()
        seen_duplicates: set[str] = set()

        for i, raw in enumerate(raw_rows, start=2):  # row 1 is header
            row_errors: list[ImportRowError] = []

            title = raw.get("title")
            if not title:
                errors.append(
                    ImportRowError(row=i, field="Название", message="Обязательное поле")
                )
                continue

            title_lower = title.strip().lower()

            # Duplicate within batch or in DB — warning, not blocker
            if title_lower in seen_titles or title_lower in existing_titles:
                if title_lower not in seen_duplicates:
                    seen_duplicates.add(title_lower)
                    duplicates.append(title)
            seen_titles.add(title_lower)

            direction_id = None
            if raw.get("direction_name"):
                direction_id = self._directions.get(raw["direction_name"].lower())
                if direction_id is None:
                    row_errors.append(
                        ImportRowError(
                            row=i,
                            field="Направление",
                            message=f"Значение '{raw['direction_name']}' не найдено в справочнике",
                        )
                    )

            priority_direction_id = None
            if raw.get("priority_direction_name"):
                priority_direction_id = self._priority_directions.get(
                    raw["priority_direction_name"].lower()
                )
                if priority_direction_id is None:
                    row_errors.append(
                        ImportRowError(
                            row=i,
                            field="Приоритетное направление",
                            message=(
                                f"Значение '{raw['priority_direction_name']}'"
                                " не найдено в справочнике"
                            ),
                        )
                    )

            trl_id = None
            if raw.get("trl_name"):
                trl_id = self._trl_levels.get(raw["trl_name"].lower())
                if trl_id is None:
                    row_errors.append(
                        ImportRowError(
                            row=i,
                            field="УГТ",
                            message=f"Значение '{raw['trl_name']}' не найдено в справочнике",
                        )
                    )

            if row_errors:
                errors.extend(row_errors)
                continue

            valid_rows.append(
                ParsedRow(
                    title=title,
                    problem=raw.get("problem"),
                    goal=raw.get("goal"),
                    expected_result=raw.get("expected_result"),
                    is_ongoing=_parse_bool(raw.get("is_ongoing_raw")),
                    direction_id=direction_id,
                    priority_direction_id=priority_direction_id,
                    trl_id=trl_id,
                )
            )

        preview = ImportPreviewResponse(
            valid_count=len(valid_rows),
            error_count=len(errors),
            errors=errors,
            duplicates=duplicates,
        )
        return valid_rows, preview

    async def do_import(self, valid_rows: list[ParsedRow]) -> int:
        projects = [
            Project(
                title=row.title,
                problem=row.problem,
                goal=row.goal,
                expected_result=row.expected_result,
                is_ongoing=row.is_ongoing,
                direction_id=row.direction_id,
                priority_direction_id=row.priority_direction_id,
                trl_id=row.trl_id,
                source=ProjectSource.auto,
            )
            for row in valid_rows
        ]
        self.session.add_all(projects)
        await self.session.commit()
        # NOTE: bulk_generate_embeddings Celery task will be triggered in TASK-012
        return len(projects)
