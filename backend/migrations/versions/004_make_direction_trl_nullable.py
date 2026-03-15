"""make direction_id and trl_id nullable for imported projects

Revision ID: 004
Revises: 003
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop RESTRICT FK constraints and recreate as SET NULL + nullable
    op.drop_constraint("projects_direction_id_fkey", "projects", type_="foreignkey")
    op.drop_constraint("projects_trl_id_fkey", "projects", type_="foreignkey")

    op.alter_column("projects", "direction_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("projects", "trl_id", existing_type=sa.UUID(), nullable=True)

    op.create_foreign_key(
        "projects_direction_id_fkey",
        "projects",
        "directions",
        ["direction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "projects_trl_id_fkey",
        "projects",
        "trl_levels",
        ["trl_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Assign fallback values before making NOT NULL again
    op.execute(
        "UPDATE projects SET direction_id = (SELECT id FROM directions LIMIT 1) "
        "WHERE direction_id IS NULL"
    )
    op.execute(
        "UPDATE projects SET trl_id = (SELECT id FROM trl_levels LIMIT 1) "
        "WHERE trl_id IS NULL"
    )

    op.drop_constraint("projects_direction_id_fkey", "projects", type_="foreignkey")
    op.drop_constraint("projects_trl_id_fkey", "projects", type_="foreignkey")

    op.alter_column("projects", "direction_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("projects", "trl_id", existing_type=sa.UUID(), nullable=False)

    op.create_foreign_key(
        "projects_direction_id_fkey",
        "projects",
        "directions",
        ["direction_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "projects_trl_id_fkey",
        "projects",
        "trl_levels",
        ["trl_id"],
        ["id"],
        ondelete="RESTRICT",
    )
