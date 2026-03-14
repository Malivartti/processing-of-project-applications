from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.services.clustering import ClusteringService, run_auto_grouping

# ---------------------------------------------------------------------------
# ClusteringService.cosine_similarity_matrix
# ---------------------------------------------------------------------------


class TestCosineSimMatrix:
    def test_shape(self):
        embeddings = np.random.rand(5, 312).astype(np.float32)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        assert matrix.shape == (5, 5)

    def test_diagonal_is_one(self):
        embeddings = np.random.rand(4, 312).astype(np.float32)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        np.testing.assert_allclose(np.diag(matrix), np.ones(4), atol=1e-5)

    def test_symmetry(self):
        embeddings = np.random.rand(6, 312).astype(np.float32)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        np.testing.assert_allclose(matrix, matrix.T, atol=1e-6)

    def test_identical_vectors_score_one(self):
        v = np.random.rand(312).astype(np.float32)
        v = v / np.linalg.norm(v)
        embeddings = np.stack([v, v])
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        assert matrix[0, 1] == pytest.approx(1.0, abs=1e-5)

    def test_orthogonal_vectors_score_zero(self):
        v1 = np.zeros(312, dtype=np.float32)
        v2 = np.zeros(312, dtype=np.float32)
        v1[0] = 1.0
        v2[1] = 1.0
        embeddings = np.stack([v1, v2])
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        assert matrix[0, 1] == pytest.approx(0.0, abs=1e-5)


# ---------------------------------------------------------------------------
# ClusteringService.apply_rejected_pairs
# ---------------------------------------------------------------------------


class TestApplyRejectedPairs:
    def test_zeroes_out_rejected_pair(self):
        ids = [uuid.uuid4() for _ in range(3)]
        matrix = np.ones((3, 3), dtype=np.float32)
        rejected = {(ids[0], ids[1]), (ids[1], ids[0])}
        result = ClusteringService.apply_rejected_pairs(matrix, ids, rejected)
        assert result[0, 1] == 0.0
        assert result[1, 0] == 0.0
        assert result[0, 2] == 1.0  # untouched pair

    def test_empty_rejected_set_returns_same(self):
        ids = [uuid.uuid4() for _ in range(3)]
        matrix = np.ones((3, 3), dtype=np.float32)
        result = ClusteringService.apply_rejected_pairs(matrix, ids, set())
        np.testing.assert_array_equal(result, matrix)

    def test_does_not_modify_original_matrix(self):
        ids = [uuid.uuid4() for _ in range(2)]
        matrix = np.ones((2, 2), dtype=np.float32)
        original = matrix.copy()
        rejected = {(ids[0], ids[1])}
        ClusteringService.apply_rejected_pairs(matrix, ids, rejected)
        np.testing.assert_array_equal(matrix, original)

    def test_ignores_ids_not_in_project_list(self):
        ids = [uuid.uuid4() for _ in range(2)]
        matrix = np.ones((2, 2), dtype=np.float32)
        rejected = {(uuid.uuid4(), uuid.uuid4())}  # not in ids
        result = ClusteringService.apply_rejected_pairs(matrix, ids, rejected)
        np.testing.assert_array_equal(result, matrix)


# ---------------------------------------------------------------------------
# ClusteringService.cluster
# ---------------------------------------------------------------------------


def _make_clustered_embeddings(
    n_clusters: int, cluster_size: int = 3, dim: int = 312, seed: int = 0
) -> np.ndarray:
    """Create unit-normalized embeddings where intra-cluster vectors are nearly identical."""
    rng = np.random.default_rng(seed)
    vectors = []
    for _ in range(n_clusters):
        center = rng.standard_normal(dim).astype(np.float32)
        center /= np.linalg.norm(center)
        for _ in range(cluster_size):
            noise = rng.standard_normal(dim).astype(np.float32) * 0.005
            v = center + noise
            v /= np.linalg.norm(v)
            vectors.append(v)
    return np.stack(vectors)


class TestCluster:
    def test_groups_similar_projects(self):
        embeddings = _make_clustered_embeddings(n_clusters=2, cluster_size=3)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.75)
        assert len(groups) == 2
        assert all(len(g) >= 2 for g in groups)

    def test_returns_empty_for_single_project(self):
        embeddings = np.random.rand(1, 312).astype(np.float32)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.75)
        assert groups == []

    def test_returns_empty_for_zero_projects(self):
        matrix = np.zeros((0, 0), dtype=np.float32)
        groups = ClusteringService.cluster(matrix, threshold=0.75)
        assert groups == []

    def test_no_groups_for_dissimilar_projects(self):
        """Random high-dimensional vectors are nearly orthogonal — no groups at high threshold."""
        rng = np.random.default_rng(42)
        embeddings = rng.standard_normal((5, 312)).astype(np.float32)
        for i in range(len(embeddings)):
            embeddings[i] /= np.linalg.norm(embeddings[i])
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.99)
        assert len(groups) == 0

    def test_all_identical_vectors_form_one_group(self):
        rng = np.random.default_rng(1)
        v = rng.standard_normal(312).astype(np.float32)
        v /= np.linalg.norm(v)
        embeddings = np.stack([v, v, v, v])
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.75)
        assert len(groups) == 1
        assert len(groups[0]) == 4

    def test_three_clusters(self):
        embeddings = _make_clustered_embeddings(n_clusters=3, cluster_size=2, seed=7)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.80)
        assert len(groups) == 3

    def test_group_indices_are_valid(self):
        embeddings = _make_clustered_embeddings(n_clusters=2, cluster_size=3)
        n = len(embeddings)
        matrix = ClusteringService.cosine_similarity_matrix(embeddings)
        groups = ClusteringService.cluster(matrix, threshold=0.75)
        for g in groups:
            assert all(0 <= idx < n for idx in g)


# ---------------------------------------------------------------------------
# run_auto_grouping — unit tests with mocked session
# ---------------------------------------------------------------------------


def _make_mock_project(embedding: list[float] | None = None, is_selected: bool = False):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.embedding = embedding or list(np.random.rand(312).astype(float))
    p.is_selected = is_selected
    p.group_id = None
    return p


def _make_session_returning(projects, rejected_pairs=None, old_groups=None):
    """Build a mock sync session where execute() chains return expected results."""
    session = MagicMock()
    rejected_pairs = rejected_pairs or []
    old_groups = old_groups or []

    call_count = [0]

    def execute_side_effect(stmt, *args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()

        c = call_count[0]
        call_count[0] += 1

        if c == 0:
            # First call: load projects with embeddings
            scalars.all.return_value = projects
        elif c == 1:
            # Second call: load rejected pairs
            scalars.all.return_value = rejected_pairs
        elif c == 2:
            # Third call: load old unconfirmed auto-groups
            scalars.all.return_value = old_groups
        else:
            # Further calls: upserts / bulk updates
            scalars.all.return_value = []

        result.scalars.return_value = scalars
        return result

    session.execute.side_effect = execute_side_effect
    return session


class TestRunAutoGrouping:
    def test_not_enough_projects_returns_zeros(self):
        session = _make_session_returning(projects=[])
        result = run_auto_grouping(session, threshold=0.75, context="main")
        assert result == {"projects_processed": 0, "groups_found": 0, "projects_in_groups": 0}

    def test_one_project_returns_zeros(self):
        p = _make_mock_project()
        session = _make_session_returning(projects=[p])
        result = run_auto_grouping(session, threshold=0.75, context="main")
        assert result["projects_processed"] == 1
        assert result["groups_found"] == 0
        assert result["projects_in_groups"] == 0

    def test_similar_projects_are_grouped(self):
        """Two nearly identical embeddings should form one group."""
        rng = np.random.default_rng(99)
        v = rng.standard_normal(312).astype(np.float32)
        v /= np.linalg.norm(v)

        def make_near(base: np.ndarray) -> list[float]:
            noise = rng.standard_normal(len(base)).astype(np.float32) * 0.001
            r = base + noise
            r /= np.linalg.norm(r)
            return r.tolist()

        projects = [_make_mock_project(embedding=make_near(v)) for _ in range(3)]
        session = _make_session_returning(projects=projects)
        result = run_auto_grouping(session, threshold=0.75, context="main")
        assert result["projects_processed"] == 3
        assert result["groups_found"] == 1
        assert result["projects_in_groups"] == 3

    def test_grouping_run_id_passed_through(self):
        """grouping_run_id parameter is accepted without error."""
        p = _make_mock_project()
        session = _make_session_returning(projects=[p])
        run_id = uuid.uuid4()
        result = run_auto_grouping(session, threshold=0.75, context="main", grouping_run_id=run_id)
        assert result["projects_processed"] == 1
