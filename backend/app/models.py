import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectSource(str, enum.Enum):
    manual = "manual"
    auto = "auto"


class GroupSource(str, enum.Enum):
    manual = "manual"
    auto = "auto"


class GroupContext(str, enum.Enum):
    main = "main"
    selection = "selection"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Stopword(Base):
    __tablename__ = "stopwords"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Direction(Base):
    __tablename__ = "directions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="direction")


class PriorityDirection(Base):
    __tablename__ = "priority_directions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="priority_direction"
    )


class TRLLevel(Base):
    __tablename__ = "trl_levels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="trl_level")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[GroupSource] = mapped_column(
        Enum(GroupSource, name="group_source_enum"), nullable=False
    )
    context: Mapped[GroupContext] = mapped_column(
        Enum(GroupContext, name="group_context_enum"), nullable=False, default=GroupContext.main
    )
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="group")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Обязательные поля формы ---
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    direction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directions.id", ondelete="SET NULL"), nullable=True
    )
    is_ongoing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Принадлежность к приоритетному направлению (необязательное)
    priority_direction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("priority_directions.id", ondelete="SET NULL"),
        nullable=True,
    )
    implementation_period: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relevance: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    key_tasks: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    trl_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trl_levels.id", ondelete="SET NULL"), nullable=True
    )
    budget: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # --- Чекбоксы: образовательные и экспертные ресурсы ---
    support_master_classes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_consultations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Чекбоксы: инфраструктура и оборудование ---
    support_equipment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_product_samples: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_materials: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_software_licenses: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Чекбоксы: рабочие площадки и стажировки ---
    support_project_site: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_internship: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Уточнение нефинансовой поддержки (необязательное) ---
    non_financial_support: Mapped[str | None] = mapped_column(Text, nullable=True)

    participants_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Системные поля ---
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_auto_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[ProjectSource] = mapped_column(
        Enum(ProjectSource, name="project_source_enum"),
        nullable=False,
        default=ProjectSource.manual,
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(312), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    direction: Mapped[Direction | None] = relationship("Direction", back_populates="projects")
    priority_direction: Mapped[PriorityDirection | None] = relationship(
        "PriorityDirection", back_populates="projects"
    )
    trl_level: Mapped[TRLLevel | None] = relationship("TRLLevel", back_populates="projects")
    group: Mapped[Group | None] = relationship("Group", back_populates="projects")

    __table_args__ = (
        Index(
            "ix_projects_fts",
            sa.text(
                "to_tsvector('russian', "
                "coalesce(title,'') || ' ' || coalesce(relevance,'') || ' ' || "
                "coalesce(problem,'') || ' ' || coalesce(goal,'') || ' ' || "
                "coalesce(key_tasks,'') || ' ' || coalesce(expected_result,''))"
            ),
            postgresql_using="gin",
        ),
    )


class GroupingRun(Base):
    __tablename__ = "grouping_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    context: Mapped[GroupContext] = mapped_column(
        Enum(GroupContext, name="group_context_enum"),
        nullable=False,
        default=GroupContext.main,
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status_enum"), nullable=False, default=RunStatus.pending
    )
    projects_processed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    groups_found: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    projects_in_groups: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    similarity_scores: Mapped[list["SimilarityScore"]] = relationship(
        "SimilarityScore", back_populates="grouping_run", foreign_keys="SimilarityScore.grouping_run_id"
    )


class SimilarityScore(Base):
    __tablename__ = "similarity_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    project_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    grouping_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grouping_runs.id", ondelete="SET NULL"), nullable=True
    )

    project_a: Mapped["Project"] = relationship("Project", foreign_keys=[project_a_id])
    project_b: Mapped["Project"] = relationship("Project", foreign_keys=[project_b_id])
    grouping_run: Mapped["GroupingRun | None"] = relationship(
        "GroupingRun",
        back_populates="similarity_scores",
        foreign_keys=[grouping_run_id],
    )

    __table_args__ = (
        UniqueConstraint("project_a_id", "project_b_id", name="uq_similarity_scores_pair"),
    )


class RejectedPair(Base):
    __tablename__ = "rejected_pairs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    project_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    project_a: Mapped["Project"] = relationship("Project", foreign_keys=[project_a_id])
    project_b: Mapped["Project"] = relationship("Project", foreign_keys=[project_b_id])
