"""005_update_structure

Update directions to match new Excel template and change
implementation_period from VARCHAR to INTEGER.

Revision ID: 005
Revises: 004
Create Date: 2026-03-24
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

NEW_DIRECTIONS = [
    "IT",
    "Дизайн",
    "Мультимедиа",
    "Научные проекты",
    "Проекты технологического лидерства",
    "Соцтех",
    "Стратегические проекты вуза",
    "Технология",
    "Транспорт",
    "Урбанистика",
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Change implementation_period from VARCHAR(100) to INTEGER
    conn.execute(
        sa.text(
            "ALTER TABLE projects ALTER COLUMN implementation_period TYPE INTEGER "
            "USING CASE WHEN implementation_period ~ '^[0-9]+$' "
            "THEN implementation_period::INTEGER ELSE 0 END"
        )
    )

    # 2. Replace directions
    conn.execute(sa.text("UPDATE projects SET direction_id = NULL WHERE direction_id IN (SELECT id FROM directions)"))
    conn.execute(sa.text("DELETE FROM directions"))

    now = datetime.now(timezone.utc)
    for name in NEW_DIRECTIONS:
        conn.execute(
            sa.text(
                "INSERT INTO directions (id, name, is_active, created_at) "
                "VALUES (:id, :name, :is_active, :created_at)"
            ),
            {"id": str(uuid.uuid4()), "name": name, "is_active": True, "created_at": now},
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Revert implementation_period back to VARCHAR
    conn.execute(
        sa.text(
            "ALTER TABLE projects ALTER COLUMN implementation_period TYPE VARCHAR(100) "
            "USING implementation_period::VARCHAR"
        )
    )

    # Restore original directions (projects lose direction refs)
    conn.execute(sa.text("UPDATE projects SET direction_id = NULL"))
    conn.execute(sa.text("DELETE FROM directions"))

    OLD_DIRECTIONS = [
        "Информационные технологии",
        "Биомедицина и здравоохранение",
        "Энергетика и ресурсосбережение",
        "Транспорт и логистика",
        "Образование и просвещение",
        "Экология и природопользование",
    ]
    now = datetime.now(timezone.utc)
    for name in OLD_DIRECTIONS:
        conn.execute(
            sa.text(
                "INSERT INTO directions (id, name, is_active, created_at) "
                "VALUES (:id, :name, :is_active, :created_at)"
            ),
            {"id": str(uuid.uuid4()), "name": name, "is_active": True, "created_at": now},
        )
