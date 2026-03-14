from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

MODEL_NAME = "cointegrated/rubert-tiny2"


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
