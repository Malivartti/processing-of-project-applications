"""001_initial

Revision ID: 001
Revises:
Create Date: 2026-03-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # directions
    op.create_table(
        "directions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # priority_directions
    op.create_table(
        "priority_directions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # trl_levels
    op.create_table(
        "trl_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ENUM types
    group_source_enum = postgresql.ENUM("manual", "auto", name="group_source_enum", create_type=False)
    group_source_enum.create(op.get_bind(), checkfirst=True)

    group_context_enum = postgresql.ENUM(
        "main", "selection", name="group_context_enum", create_type=False
    )
    group_context_enum.create(op.get_bind(), checkfirst=True)

    project_source_enum = postgresql.ENUM(
        "manual", "auto", name="project_source_enum", create_type=False
    )
    project_source_enum.create(op.get_bind(), checkfirst=True)

    run_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed", name="run_status_enum", create_type=False
    )
    run_status_enum.create(op.get_bind(), checkfirst=True)

    # groups
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("manual", "auto", name="group_source_enum", create_constraint=False),
            nullable=False,
        ),
        sa.Column(
            "context",
            sa.Enum("main", "selection", name="group_context_enum", create_constraint=False),
            nullable=False,
            server_default="main",
        ),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # grouping_runs
    op.create_table(
        "grouping_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column(
            "context",
            sa.Enum("main", "selection", name="group_context_enum", create_constraint=False),
            nullable=False,
            server_default="main",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                name="run_status_enum",
                create_constraint=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("projects_processed", sa.BigInteger(), nullable=True),
        sa.Column("groups_found", sa.BigInteger(), nullable=True),
        sa.Column("projects_in_groups", sa.BigInteger(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("problem", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=True),
        sa.Column("is_ongoing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_auto_checked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "source",
            sa.Enum("manual", "auto", name="project_source_enum", create_constraint=False),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "direction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("directions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "priority_direction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("priority_directions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "trl_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trl_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("embedding", sa.Text(), nullable=True),  # placeholder; vector type set below
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Replace placeholder with actual vector column
    op.execute("ALTER TABLE projects DROP COLUMN embedding")
    op.execute("ALTER TABLE projects ADD COLUMN embedding vector(312)")

    # GIN index for full-text search (Russian)
    op.execute(
        """
        CREATE INDEX ix_projects_fts ON projects
        USING gin (
            to_tsvector(
                'russian',
                coalesce(title, '') || ' ' ||
                coalesce(problem, '') || ' ' ||
                coalesce(goal, '') || ' ' ||
                coalesce(expected_result, '')
            )
        )
        """
    )

    # similarity_scores
    op.create_table(
        "similarity_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "grouping_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grouping_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("project_a_id", "project_b_id", name="uq_similarity_scores_pair"),
    )

    # rejected_pairs
    op.create_table(
        "rejected_pairs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("rejected_pairs")
    op.drop_table("similarity_scores")
    op.execute("DROP INDEX IF EXISTS ix_projects_fts")
    op.drop_table("projects")
    op.drop_table("grouping_runs")
    op.drop_table("groups")
    op.drop_table("trl_levels")
    op.drop_table("priority_directions")
    op.drop_table("directions")

    op.execute("DROP TYPE IF EXISTS run_status_enum")
    op.execute("DROP TYPE IF EXISTS project_source_enum")
    op.execute("DROP TYPE IF EXISTS group_context_enum")
    op.execute("DROP TYPE IF EXISTS group_source_enum")
