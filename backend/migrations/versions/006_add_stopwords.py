"""006_add_stopwords

Create stopwords table with domain-specific words for group name generation.

Revision ID: 006
Revises: 005
Create Date: 2026-03-24
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

# Domain-specific words common across all project applications
INITIAL_STOPWORDS = [
    "разработка",
    "создание",
    "проект",
    "исследование",
    "система",
    "разработать",
    "создать",
    "исследовать",
    "внедрение",
    "реализация",
    "повышение",
    "улучшение",
    "обеспечение",
    "применение",
    "использование",
]


def upgrade() -> None:
    op.create_table(
        "stopwords",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    conn = op.get_bind()
    now = datetime.now(timezone.utc)
    for word in INITIAL_STOPWORDS:
        conn.execute(
            sa.text(
                "INSERT INTO stopwords (id, name, is_active, created_at) "
                "VALUES (:id, :name, :is_active, :created_at)"
            ),
            {"id": str(uuid.uuid4()), "name": word, "is_active": True, "created_at": now},
        )


def downgrade() -> None:
    op.drop_table("stopwords")
