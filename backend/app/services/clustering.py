from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Callable

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity


class ClusteringService:
    @staticmethod
    def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix (N x N, values in [-1, 1])."""
        return cosine_similarity(embeddings)

    @staticmethod
    def apply_rejected_pairs(
        similarity_matrix: np.ndarray,
        project_ids: list[uuid.UUID],
        rejected_set: set[tuple[uuid.UUID, uuid.UUID]],
    ) -> np.ndarray:
        """Zero out similarity for rejected pairs so they won't be clustered together."""
        if not rejected_set:
            return similarity_matrix
        id_to_idx = {pid: i for i, pid in enumerate(project_ids)}
        matrix = similarity_matrix.copy()
        for a_id, b_id in rejected_set:
            ai = id_to_idx.get(a_id)
            bi = id_to_idx.get(b_id)
            if ai is not None and bi is not None:
                matrix[ai, bi] = 0.0
                matrix[bi, ai] = 0.0
        return matrix

    @staticmethod
    def cluster(
        similarity_matrix: np.ndarray,
        threshold: float,
    ) -> list[list[int]]:
        """Run agglomerative clustering.

        distance_threshold = 1 - threshold: projects with similarity >= threshold
        are considered similar enough to group.

        Returns groups (lists of project indices) with >= 2 members.
        """
        n = len(similarity_matrix)
        if n < 2:
            return []

        distance_matrix = 1.0 - similarity_matrix
        np.clip(distance_matrix, 0.0, 2.0, out=distance_matrix)
        np.fill_diagonal(distance_matrix, 0.0)

        model = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=1.0 - threshold,
        )
        labels = model.fit_predict(distance_matrix)

        clusters: dict[int, list[int]] = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[label].append(idx)

        return [indices for indices in clusters.values() if len(indices) >= 2]


def run_auto_grouping(
    session,  # sync SQLAlchemy Session
    threshold: float,
    context: str,
    grouping_run_id: uuid.UUID | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict:
    """Full auto-grouping pipeline. Saves results to DB.

    Steps:
    1. Load projects with embeddings (filtered by context for 'selection').
    2. Load rejected pairs.
    3. Compute cosine similarity matrix.
    4. Zero out rejected pairs in the matrix.
    5. Run agglomerative clustering.
    6. Delete old unconfirmed auto-groups for this context.
    7. Create new groups, save similarity_scores, update project group_ids.
    8. Mark all processed projects as is_auto_checked=True.

    Returns:
        dict with projects_processed, groups_found, projects_in_groups.
    """
    import sqlalchemy as sa
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.models import (
        Group,
        GroupContext,
        GroupSource,
        Project,
        RejectedPair,
        SimilarityScore,
    )

    ctx = GroupContext(context)

    # 1. Load projects with embeddings
    query = sa.select(Project).where(Project.embedding.is_not(None))
    if ctx == GroupContext.selection:
        query = query.where(Project.is_selected.is_(True))
    projects: list[Project] = list(session.execute(query).scalars().all())

    if progress_callback is not None:
        progress_callback("embeddings", len(projects), len(projects))

    if len(projects) < 2:
        if projects:
            session.execute(
                sa.update(Project)
                .where(Project.id.in_([p.id for p in projects]))
                .values(is_auto_checked=True)
            )
            session.commit()
        return {
            "projects_processed": len(projects),
            "groups_found": 0,
            "projects_in_groups": 0,
        }

    project_ids = [p.id for p in projects]

    # 2. Load rejected pairs involving any of these projects
    rp_rows: list[RejectedPair] = list(
        session.execute(
            sa.select(RejectedPair).where(
                sa.or_(
                    RejectedPair.project_a_id.in_(project_ids),
                    RejectedPair.project_b_id.in_(project_ids),
                )
            )
        ).scalars().all()
    )
    rejected_set: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for rp in rp_rows:
        rejected_set.add((rp.project_a_id, rp.project_b_id))
        rejected_set.add((rp.project_b_id, rp.project_a_id))

    # 3. Build embedding matrix
    embeddings = np.array([p.embedding for p in projects], dtype=np.float32)

    # 4. Compute similarity matrix and apply rejected pairs
    sim_matrix = ClusteringService.cosine_similarity_matrix(embeddings)
    sim_matrix = ClusteringService.apply_rejected_pairs(sim_matrix, project_ids, rejected_set)

    if progress_callback is not None:
        progress_callback("similarity", 1, 1)

    # 5. Cluster
    groups_indices = ClusteringService.cluster(sim_matrix, threshold)

    if progress_callback is not None:
        progress_callback("clustering", 1, 1)

    # 6. Delete old unconfirmed auto-groups for this context
    old_groups: list[Group] = list(
        session.execute(
            sa.select(Group).where(
                Group.source == GroupSource.auto,
                Group.context == ctx,
                Group.is_confirmed.is_(False),
            )
        ).scalars().all()
    )
    for old_group in old_groups:
        session.execute(
            sa.update(Project).where(Project.group_id == old_group.id).values(group_id=None)
        )
        session.delete(old_group)
    session.flush()

    # 7. Create new groups, save similarity scores, update project group_ids
    total_groups = len(groups_indices)
    projects_in_groups = 0
    for i, group_indices in enumerate(groups_indices):
        if progress_callback is not None:
            progress_callback("saving", i, total_groups)
        group_projects = [projects[idx] for idx in group_indices]
        group = Group(
            name=f"Авто-группа {i + 1}",
            source=GroupSource.auto,
            context=ctx,
            is_confirmed=False,
        )
        session.add(group)
        session.flush()  # get group.id before commit

        for p in group_projects:
            p.group_id = group.id

        projects_in_groups += len(group_projects)

        # Save pairwise similarity scores within this group (upsert)
        for ai_pos in range(len(group_indices)):
            for bi_pos in range(ai_pos + 1, len(group_indices)):
                pa_id = projects[group_indices[ai_pos]].id
                pb_id = projects[group_indices[bi_pos]].id
                score = float(sim_matrix[group_indices[ai_pos], group_indices[bi_pos]])
                stmt = (
                    pg_insert(SimilarityScore)
                    .values(
                        id=uuid.uuid4(),
                        project_a_id=pa_id,
                        project_b_id=pb_id,
                        score=score,
                        grouping_run_id=grouping_run_id,
                    )
                    .on_conflict_do_update(
                        constraint="uq_similarity_scores_pair",
                        set_={"score": score, "grouping_run_id": grouping_run_id},
                    )
                )
                session.execute(stmt)

    # 8. Mark all processed projects as auto_checked
    session.execute(
        sa.update(Project)
        .where(Project.id.in_(project_ids))
        .values(is_auto_checked=True)
    )
    session.commit()

    return {
        "projects_processed": len(projects),
        "groups_found": len(groups_indices),
        "projects_in_groups": projects_in_groups,
    }
