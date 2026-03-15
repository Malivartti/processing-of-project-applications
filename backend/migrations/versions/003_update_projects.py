"""update projects: add required fields, tighten constraints

Revision ID: 003
Revises: 002
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Shrink title column to 80 chars (truncate existing data to fit)
    op.execute("UPDATE projects SET title = LEFT(title, 80) WHERE LENGTH(title) > 80")
    op.alter_column("projects", "title", type_=sa.String(80), existing_nullable=False)

    # 2. Add new required text fields (nullable first, fill defaults, then set NOT NULL)
    op.add_column("projects", sa.Column("implementation_period", sa.String(100), nullable=True))
    op.add_column("projects", sa.Column("relevance", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("key_tasks", sa.Text(), nullable=True))

    op.execute("UPDATE projects SET implementation_period = '' WHERE implementation_period IS NULL")
    op.execute("UPDATE projects SET relevance = '' WHERE relevance IS NULL")
    op.execute("UPDATE projects SET key_tasks = '' WHERE key_tasks IS NULL")

    op.alter_column("projects", "implementation_period", nullable=False)
    op.alter_column("projects", "relevance", nullable=False)
    op.alter_column("projects", "key_tasks", nullable=False)

    # 3. Make previously nullable text fields NOT NULL
    op.execute("UPDATE projects SET problem = '' WHERE problem IS NULL")
    op.execute("UPDATE projects SET goal = '' WHERE goal IS NULL")
    op.execute("UPDATE projects SET expected_result = '' WHERE expected_result IS NULL")
    op.alter_column("projects", "problem", existing_type=sa.Text(), nullable=False)
    op.alter_column("projects", "goal", existing_type=sa.Text(), nullable=False)
    op.alter_column("projects", "expected_result", existing_type=sa.Text(), nullable=False)

    # 4. Add new numeric and boolean fields with server defaults
    op.add_column("projects", sa.Column("budget", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("projects", sa.Column("participants_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("projects", sa.Column("support_master_classes", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_consultations", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_equipment", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_product_samples", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_materials", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_software_licenses", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_project_site", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("support_internship", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("non_financial_support", sa.Text(), nullable=True))

    # 5. Make direction_id and trl_id NOT NULL
    #    If existing rows have NULLs, assign a fallback from the dictionary tables.
    op.execute(
        "UPDATE projects SET direction_id = (SELECT id FROM directions LIMIT 1) "
        "WHERE direction_id IS NULL"
    )
    op.execute(
        "UPDATE projects SET trl_id = (SELECT id FROM trl_levels LIMIT 1) "
        "WHERE trl_id IS NULL"
    )
    op.alter_column("projects", "direction_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("projects", "trl_id", existing_type=sa.UUID(), nullable=False)

    # Change ondelete for direction_id and trl_id from SET NULL to RESTRICT
    op.drop_constraint("projects_direction_id_fkey", "projects", type_="foreignkey")
    op.drop_constraint("projects_trl_id_fkey", "projects", type_="foreignkey")
    op.create_foreign_key(
        "projects_direction_id_fkey", "projects", "directions", ["direction_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "projects_trl_id_fkey", "projects", "trl_levels", ["trl_id"], ["id"],
        ondelete="RESTRICT",
    )

    # 6. Recreate FTS index with new fields
    op.drop_index("ix_projects_fts", table_name="projects", postgresql_using="gin")
    op.create_index(
        "ix_projects_fts",
        "projects",
        [
            sa.literal_column(
                "to_tsvector('russian', "
                "coalesce(title,'') || ' ' || coalesce(relevance,'') || ' ' || "
                "coalesce(problem,'') || ' ' || coalesce(goal,'') || ' ' || "
                "coalesce(key_tasks,'') || ' ' || coalesce(expected_result,''))"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_projects_fts", table_name="projects", postgresql_using="gin")
    op.create_index(
        "ix_projects_fts",
        "projects",
        [
            sa.literal_column(
                "to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(problem,'') || ' '"
                " || coalesce(goal,'') || ' ' || coalesce(expected_result,''))"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )

    op.drop_constraint("projects_direction_id_fkey", "projects", type_="foreignkey")
    op.drop_constraint("projects_trl_id_fkey", "projects", type_="foreignkey")
    op.create_foreign_key(
        "projects_direction_id_fkey", "projects", "directions", ["direction_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "projects_trl_id_fkey", "projects", "trl_levels", ["trl_id"], ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("projects", "direction_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("projects", "trl_id", existing_type=sa.UUID(), nullable=True)

    op.drop_column("projects", "non_financial_support")
    op.drop_column("projects", "support_internship")
    op.drop_column("projects", "support_project_site")
    op.drop_column("projects", "support_software_licenses")
    op.drop_column("projects", "support_materials")
    op.drop_column("projects", "support_product_samples")
    op.drop_column("projects", "support_equipment")
    op.drop_column("projects", "support_consultations")
    op.drop_column("projects", "support_master_classes")
    op.drop_column("projects", "participants_count")
    op.drop_column("projects", "budget")

    op.alter_column("projects", "problem", existing_type=sa.Text(), nullable=True)
    op.alter_column("projects", "goal", existing_type=sa.Text(), nullable=True)
    op.alter_column("projects", "expected_result", existing_type=sa.Text(), nullable=True)

    op.drop_column("projects", "key_tasks")
    op.drop_column("projects", "relevance")
    op.drop_column("projects", "implementation_period")

    op.alter_column("projects", "title", type_=sa.String(512), existing_nullable=False)
