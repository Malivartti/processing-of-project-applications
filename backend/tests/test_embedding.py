"""Tests for EmbeddingService and TextProcessingUtils (TASK-012)."""
from unittest.mock import MagicMock

import numpy as np

from app.services.embedding import EmbeddingService
from app.utils.text import TextProcessingUtils

# ---------------------------------------------------------------------------
# TextProcessingUtils
# ---------------------------------------------------------------------------


def test_prepare_text_basic():
    result = TextProcessingUtils.prepare_text("Проект ИИ", "Проблема", "Цель", "Результат")
    assert result == "проект ии проблема цель результат"


def test_prepare_text_removes_punctuation():
    result = TextProcessingUtils.prepare_text("Проект: ИИ!", "Проблема?")
    assert "!" not in result
    assert ":" not in result
    assert "?" not in result


def test_prepare_text_none_fields():
    result = TextProcessingUtils.prepare_text("Только название")
    assert result == "только название"


def test_prepare_text_collapses_whitespace():
    result = TextProcessingUtils.prepare_text("  много   пробелов  ", "  тест  ")
    assert "  " not in result
    assert result == result.strip()


def test_prepare_text_empty_optional_fields():
    result = TextProcessingUtils.prepare_text("Название", None, None, None)
    assert result == "название"


# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------


def _make_mock_model(n_texts: int = 1, dim: int = 312) -> MagicMock:
    """Return a mock SentenceTransformer that returns random vectors."""
    mock = MagicMock()
    mock.encode.return_value = np.random.rand(n_texts, dim).astype(np.float32)
    return mock


def test_embedding_service_encode_shape():
    texts = ["текст первый", "текст второй", "текст третий"]
    mock_model = _make_mock_model(n_texts=len(texts))
    svc = EmbeddingService(mock_model)
    result = svc.encode(texts)
    assert result.shape == (3, 312)


def test_embedding_service_calls_model_with_correct_args():
    texts = ["один текст"]
    mock_model = _make_mock_model(n_texts=1)
    svc = EmbeddingService(mock_model)
    svc.encode(texts)
    mock_model.encode.assert_called_once_with(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )


def test_embedding_service_returns_numpy_array():
    texts = ["тест"]
    mock_model = _make_mock_model(n_texts=1)
    svc = EmbeddingService(mock_model)
    result = svc.encode(texts)
    assert isinstance(result, np.ndarray)


# ---------------------------------------------------------------------------
# Celery task registration
# ---------------------------------------------------------------------------


def test_bulk_generate_embeddings_registered():
    import app.tasks.embeddings  # noqa: F401 — registers the task
    from app.tasks.celery_app import celery

    assert "app.tasks.embeddings.bulk_generate_embeddings" in celery.tasks


def test_bulk_generate_embeddings_skips_when_no_model():
    """When model is not loaded, task returns a skipped result."""
    from unittest.mock import patch

    from app.tasks.embeddings import bulk_generate_embeddings

    with patch("app.tasks.embeddings.get_embedding_model", return_value=None):
        result = bulk_generate_embeddings(["00000000-0000-0000-0000-000000000001"])

    assert result["skipped"] == 1
    assert result["reason"] == "model_not_loaded"
