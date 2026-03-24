from __future__ import annotations

import re
import uuid

import numpy as np
import pymorphy3
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from stop_words import get_stop_words as _get_stop_words

from app.exceptions import NotFoundError
from app.models import Project, SimilarityScore, Stopword
from app.repositories.project import ProjectRepo
from app.schemas.compare import CompareResponse
from app.services.project import ProjectService

# Parts of speech to keep: noun and verb (incl. infinitive)
_KEEP_POS = {"NOUN", "VERB", "INFN"}

# Minimum word length after lemmatisation
_MIN_LEN = 4  # > 3 chars

# Comprehensive Russian stop-words (auxiliaries / pronouns that pass POS filter)
_STOP_LEMMAS = set(_get_stop_words("russian")) | {
    # common auxiliaries that pass POS filter (VERB/INFN)
    "быть", "стать", "являться", "иметь", "делать",
    "получать", "обеспечивать", "осуществлять",
}

_WORD_RE = re.compile(r"[а-яёa-z]+", re.UNICODE | re.IGNORECASE)

_morph = pymorphy3.MorphAnalyzer()


def _extract_lemmas(text: str, extra_stop: set[str] | None = None) -> dict[str, set[str]]:
    """Return a mapping of significant lemmas → set of original tokens from *text*."""
    stop = _STOP_LEMMAS if not extra_stop else _STOP_LEMMAS | extra_stop
    lemma_tokens: dict[str, set[str]] = {}
    for token in _WORD_RE.findall(text.lower()):
        parsed = _morph.parse(token)
        if not parsed:
            continue
        best = parsed[0]
        pos = best.tag.POS
        if pos not in _KEEP_POS:
            continue
        lemma = best.normal_form
        if len(lemma) <= _MIN_LEN - 1:  # length must be > 3, i.e. >= 4
            continue
        if lemma in stop:
            continue
        lemma_tokens.setdefault(lemma, set()).add(token)
    return lemma_tokens


def _project_text(project: Project) -> str:
    parts = [
        project.title,
        project.relevance,
        project.problem,
        project.goal,
        project.key_tasks,
        project.expected_result,
    ]
    return " ".join(p for p in parts if p)


def _cosine_score(emb_a: list[float], emb_b: list[float]) -> float:
    a = np.array(emb_a, dtype=np.float32)
    b = np.array(emb_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class CompareService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProjectRepo(session)
        self.project_service = ProjectService(session)

    async def compare(self, id_a: uuid.UUID, id_b: uuid.UUID) -> CompareResponse:
        project_a = await self.repo.get_by_id(id_a)
        if project_a is None:
            raise NotFoundError(detail=f"Project {id_a} not found")
        project_b = await self.repo.get_by_id(id_b)
        if project_b is None:
            raise NotFoundError(detail=f"Project {id_b} not found")

        # Load domain-specific stopwords from DB
        result = await self.session.execute(
            select(Stopword).where(Stopword.is_active.is_(True))
        )
        db_stopwords = {row.name.lower() for row in result.scalars().all()}

        score = await self._get_score(project_a, project_b)
        keywords, highlight_tokens = _get_keywords(project_a, project_b, db_stopwords)

        return CompareResponse(
            project_a=self.project_service._to_read(project_a),
            project_b=self.project_service._to_read(project_b),
            score=score,
            keywords=keywords,
            highlight_tokens=highlight_tokens,
        )

    async def _get_score(
        self,
        project_a: Project,
        project_b: Project,
    ) -> float | None:
        # Try to find existing score in DB (order-insensitive)
        result = await self.session.execute(
            select(SimilarityScore).where(
                or_(
                    (SimilarityScore.project_a_id == project_a.id)
                    & (SimilarityScore.project_b_id == project_b.id),
                    (SimilarityScore.project_a_id == project_b.id)
                    & (SimilarityScore.project_b_id == project_a.id),
                )
            )
        )
        existing = result.scalars().first()
        if existing is not None:
            return existing.score

        # Compute on-the-fly if both embeddings are present
        if project_a.embedding is not None and project_b.embedding is not None:
            return _cosine_score(project_a.embedding, project_b.embedding)

        return None


def _get_keywords(
    project_a: Project, project_b: Project, extra_stop: set[str] | None = None
) -> tuple[list[str], list[str]]:
    """Return (keywords, highlight_tokens) for common significant lemmas.

    keywords: sorted lemmas for display.
    highlight_tokens: all original word forms from both texts that share a common lemma.
    """
    text_a = _project_text(project_a)
    text_b = _project_text(project_b)
    if not text_a or not text_b:
        return [], []
    map_a = _extract_lemmas(text_a, extra_stop)
    map_b = _extract_lemmas(text_b, extra_stop)
    common_lemmas = map_a.keys() & map_b.keys()
    tokens: set[str] = set()
    for lemma in common_lemmas:
        tokens |= map_a[lemma]
        tokens |= map_b[lemma]
    return sorted(common_lemmas), sorted(tokens)
