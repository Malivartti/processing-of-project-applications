from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

MODEL_NAME = "cointegrated/rubert-tiny2"

# Weights for each project field when computing the combined embedding.
# Higher weight = that field has more influence on similarity.
FIELD_WEIGHTS: dict[str, float] = {
    "title": 0.30,
    "goal": 0.25,
    "problem": 0.10,
    "relevance": 0.05,
    "key_tasks": 0.10,
    "expected_result": 0.20,
}


def load_sentence_transformer() -> "SentenceTransformer":
    """Load rubert-tiny2 model. Called once at Celery worker startup."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


class EmbeddingService:
    """Wraps a SentenceTransformer model for encoding project texts."""

    def __init__(self, model: "SentenceTransformer") -> None:
        self.model = model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into 312-dimensional normalised vectors.

        Returns shape (len(texts), 312).
        """
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def encode_weighted(self, fields_list: list[dict[str, str]]) -> np.ndarray:
        """Encode each project field separately and combine as weighted average.

        Each dict should have keys matching FIELD_WEIGHTS:
        title, goal, problem, relevance, key_tasks, expected_result.

        Returns normalized (N, 312) array. Fields that are empty/missing
        are replaced with a single space so the model still produces a vector.
        """
        n = len(fields_list)
        dim = 312
        combined = np.zeros((n, dim), dtype=np.float32)

        for field, weight in FIELD_WEIGHTS.items():
            texts = [d.get(field) or " " for d in fields_list]
            vecs = self.encode(texts)  # (n, dim), already normalized
            combined += weight * vecs

        norms = np.linalg.norm(combined, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        return combined / norms
