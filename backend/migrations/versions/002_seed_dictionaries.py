"""002_seed_dictionaries

Revision ID: 002
Revises: 001
Create Date: 2026-03-15
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

DIRECTIONS = [
    "Информационные технологии",
    "Биомедицина и здравоохранение",
    "Энергетика и ресурсосбережение",
    "Транспорт и логистика",
    "Образование и просвещение",
    "Экология и природопользование",
]

PRIORITY_DIRECTIONS = [
    "Цифровая экономика",
    "Здоровье и долголетие",
    "Умный город",
    "Агротехнологии",
    "Новые материалы и технологии",
    "Безопасность и противодействие угрозам",
]

TRL_LEVELS = [
    (1, "ТРЛ 1 — Базовые принципы"),
    (2, "ТРЛ 2 — Концепция технологии"),
    (3, "ТРЛ 3 — Экспериментальное подтверждение"),
    (4, "ТРЛ 4 — Лабораторный прототип"),
    (5, "ТРЛ 5 — Прототип в условиях, близких к реальным"),
    (6, "ТРЛ 6 — Прототип в реальных условиях"),
    (7, "ТРЛ 7 — Демонстрация системы"),
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for name in DIRECTIONS:
        conn.execute(
            sa.text(
                "INSERT INTO directions (id, name, is_active, created_at) "
                "VALUES (:id, :name, :is_active, :created_at)"
            ),
            {"id": str(uuid.uuid4()), "name": name, "is_active": True, "created_at": now},
        )

    for name in PRIORITY_DIRECTIONS:
        conn.execute(
            sa.text(
                "INSERT INTO priority_directions (id, name, is_active, created_at) "
                "VALUES (:id, :name, :is_active, :created_at)"
            ),
            {"id": str(uuid.uuid4()), "name": name, "is_active": True, "created_at": now},
        )

    for level, name in TRL_LEVELS:
        conn.execute(
            sa.text(
                "INSERT INTO trl_levels (id, name, level, is_active, created_at) "
                "VALUES (:id, :name, :level, :is_active, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "level": level,
                "is_active": True,
                "created_at": now,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM trl_levels"))
    conn.execute(sa.text("DELETE FROM priority_directions"))
    conn.execute(sa.text("DELETE FROM directions"))
