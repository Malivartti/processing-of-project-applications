from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.models import ProjectSource
from app.schemas.compare import CompareResponse
from app.schemas.project import ProjectRead
from app.services.compare import (
    CompareService,
    _cosine_score,
    _extract_lemmas,
    _get_keywords,
)

# ---------------------------------------------------------------------------
# Unit: _extract_lemmas
# ---------------------------------------------------------------------------


class TestExtractLemmas:
    def test_extracts_nouns(self):
        lemmas = _extract_lemmas("разработка системы управления проектами")
        # 'система', 'управление', 'проект' are nouns and should appear
        assert len(lemmas) > 0

    def test_filters_short_words(self):
        lemmas = _extract_lemmas("да нет ок вот так")
        # All are short (≤3 chars) or not NOUN/VERB — should return empty
        assert len(lemmas) == 0

    def test_returns_set(self):
        lemmas = _extract_lemmas("разработка разработка разработка")
        assert isinstance(lemmas, set)
        assert len(lemmas) == 1

    def test_empty_text(self):
        assert _extract_lemmas("") == set()


# ---------------------------------------------------------------------------
# Unit: _cosine_score
# ---------------------------------------------------------------------------


class TestCosineScore:
    def test_identical_vectors(self):
        v = np.ones(312, dtype=np.float32)
        assert _cosine_score(v.tolist(), v.tolist()) == pytest.approx(1.0, abs=1e-5)

    def test_zero_vector_returns_zero(self):
        v = np.zeros(312, dtype=np.float32)
        w = np.ones(312, dtype=np.float32)
        assert _cosine_score(v.tolist(), w.tolist()) == 0.0

    def test_orthogonal_vectors(self):
        a = [1.0] + [0.0] * 311
        b = [0.0, 1.0] + [0.0] * 310
        assert _cosine_score(a, b) == pytest.approx(0.0, abs=1e-5)


# ---------------------------------------------------------------------------
# Unit: _get_keywords
# ---------------------------------------------------------------------------


def _mock_project(title="", problem=None, goal=None, expected_result=None):
    p = MagicMock()
    p.title = title
    p.problem = problem
    p.goal = goal
    p.expected_result = expected_result
    return p


class TestGetKeywords:
    def test_common_keywords_found(self):
        p_a = _mock_project(title="разработка системы управления данными")
        p_b = _mock_project(title="разработка системы обработки данных")
        kw = _get_keywords(p_a, p_b)
        assert isinstance(kw, list)
        # "разработка", "система", "данные" should be common
        assert len(kw) > 0

    def test_empty_texts_return_empty(self):
        p_a = _mock_project(title="")
        p_b = _mock_project(title="")
        assert _get_keywords(p_a, p_b) == []

    def test_no_common_words(self):
        p_a = _mock_project(title="яблоко фрукты питание")
        p_b = _mock_project(title="автомобиль двигатель колесо")
        kw = _get_keywords(p_a, p_b)
        assert isinstance(kw, list)

    def test_result_is_sorted(self):
        p_a = _mock_project(title="создание разработка внедрение системы управления данными")
        p_b = _mock_project(title="разработка системы управления данными создание внедрение")
        kw = _get_keywords(p_a, p_b)
        assert kw == sorted(kw)


# ---------------------------------------------------------------------------
# Integration: CompareService (mocked DB)
# ---------------------------------------------------------------------------


def _make_project_read(title="Test"):
    return ProjectRead(
        id=uuid.uuid4(),
        title=title,
        problem="Описание проблемы",
        goal="Цель проекта",
        expected_result="Ожидаемый результат",
        is_ongoing=False,
        is_selected=False,
        is_auto_checked=False,
        source=ProjectSource.manual,
        direction_id=None,
        direction_name=None,
        priority_direction_id=None,
        priority_direction_name=None,
        trl_id=None,
        trl_name=None,
        group=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestCompareService:
    @pytest.mark.asyncio
    async def test_compare_returns_score_from_db(self):
        """When SimilarityScore exists in DB, it is used directly."""
        pa_id = uuid.uuid4()
        pb_id = uuid.uuid4()
        pa_read = _make_project_read("A")
        pb_read = _make_project_read("B")

        mock_session = MagicMock()

        with (
            patch("app.services.compare.ProjectRepo") as MockRepo,
            patch("app.services.compare.ProjectService") as MockSvc,
        ):
            pa_orm = MagicMock()
            pa_orm.id = pa_id
            pa_orm.title = "A"
            pa_orm.problem = None
            pa_orm.goal = None
            pa_orm.expected_result = None
            pa_orm.embedding = None

            pb_orm = MagicMock()
            pb_orm.id = pb_id
            pb_orm.title = "B"
            pb_orm.problem = None
            pb_orm.goal = None
            pb_orm.expected_result = None
            pb_orm.embedding = None

            mock_repo = AsyncMock()
            mock_repo.get_by_id.side_effect = [pa_orm, pb_orm]
            MockRepo.return_value = mock_repo

            mock_ps = MagicMock()
            mock_ps._to_read.side_effect = [pa_read, pb_read]
            MockSvc.return_value = mock_ps

            # Simulate DB score row
            score_row = MagicMock()
            score_row.score = 0.87
            db_result = MagicMock()
            db_result.scalar_one_or_none.return_value = score_row
            mock_session.execute = AsyncMock(return_value=db_result)

            svc = CompareService(mock_session)
            result = await svc.compare(pa_id, pb_id)

        assert result.score == pytest.approx(0.87)

    @pytest.mark.asyncio
    async def test_compare_computes_score_on_the_fly(self):
        """When no DB score, cosine similarity is computed from embeddings."""
        pa_id = uuid.uuid4()
        pb_id = uuid.uuid4()
        pa_read = _make_project_read("A")
        pb_read = _make_project_read("B")

        emb = np.ones(312, dtype=np.float32).tolist()

        mock_session = MagicMock()

        with (
            patch("app.services.compare.ProjectRepo") as MockRepo,
            patch("app.services.compare.ProjectService") as MockSvc,
        ):
            pa_orm = MagicMock()
            pa_orm.id = pa_id
            pa_orm.title = "A"
            pa_orm.problem = None
            pa_orm.goal = None
            pa_orm.expected_result = None
            pa_orm.embedding = emb

            pb_orm = MagicMock()
            pb_orm.id = pb_id
            pb_orm.title = "B"
            pb_orm.problem = None
            pb_orm.goal = None
            pb_orm.expected_result = None
            pb_orm.embedding = emb

            mock_repo = AsyncMock()
            mock_repo.get_by_id.side_effect = [pa_orm, pb_orm]
            MockRepo.return_value = mock_repo

            mock_ps = MagicMock()
            mock_ps._to_read.side_effect = [pa_read, pb_read]
            MockSvc.return_value = mock_ps

            # No DB score row
            db_result = MagicMock()
            db_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=db_result)

            svc = CompareService(mock_session)
            result = await svc.compare(pa_id, pb_id)

        assert result.score == pytest.approx(1.0, abs=1e-5)

    @pytest.mark.asyncio
    async def test_compare_returns_none_score_when_no_embeddings(self):
        pa_id = uuid.uuid4()
        pb_id = uuid.uuid4()
        pa_read = _make_project_read("A")
        pb_read = _make_project_read("B")

        mock_session = MagicMock()

        with (
            patch("app.services.compare.ProjectRepo") as MockRepo,
            patch("app.services.compare.ProjectService") as MockSvc,
        ):
            pa_orm = MagicMock()
            pa_orm.id = pa_id
            pa_orm.title = "разработка системы"
            pa_orm.problem = None
            pa_orm.goal = None
            pa_orm.expected_result = None
            pa_orm.embedding = None

            pb_orm = MagicMock()
            pb_orm.id = pb_id
            pb_orm.title = "создание платформы"
            pb_orm.problem = None
            pb_orm.goal = None
            pb_orm.expected_result = None
            pb_orm.embedding = None

            mock_repo = AsyncMock()
            mock_repo.get_by_id.side_effect = [pa_orm, pb_orm]
            MockRepo.return_value = mock_repo

            mock_ps = MagicMock()
            mock_ps._to_read.side_effect = [pa_read, pb_read]
            MockSvc.return_value = mock_ps

            db_result = MagicMock()
            db_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=db_result)

            svc = CompareService(mock_session)
            result = await svc.compare(pa_id, pb_id)

        assert result.score is None
        assert isinstance(result.keywords, list)

    @pytest.mark.asyncio
    async def test_compare_raises_not_found_for_missing_project(self):
        from app.exceptions import NotFoundError

        pa_id = uuid.uuid4()
        pb_id = uuid.uuid4()
        mock_session = MagicMock()

        with patch("app.services.compare.ProjectRepo") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            MockRepo.return_value = mock_repo

            svc = CompareService(mock_session)
            with pytest.raises(NotFoundError):
                await svc.compare(pa_id, pb_id)


# ---------------------------------------------------------------------------
# API endpoint: GET /api/projects/compare
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compare_endpoint_returns_200():
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    pa_id = uuid.uuid4()
    pb_id = uuid.uuid4()
    pa_read = _make_project_read("A")
    pb_read = _make_project_read("B")

    mock_response = CompareResponse(
        project_a=pa_read,
        project_b=pb_read,
        score=0.75,
        keywords=["система", "разработка"],
    )

    async def override_db():
        yield MagicMock()

    with patch("app.api.projects.CompareService") as MockSvc:
        instance = AsyncMock()
        instance.compare.return_value = mock_response
        MockSvc.return_value = instance

        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/projects/compare?a={pa_id}&b={pb_id}")
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == pytest.approx(0.75)
    assert "система" in data["keywords"]


@pytest.mark.asyncio
async def test_compare_endpoint_missing_param_returns_422():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/projects/compare?a=" + str(uuid.uuid4()))

    assert resp.status_code == 422
