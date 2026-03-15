from __future__ import annotations

import re
import uuid

import numpy as np
import pymorphy3
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Project, SimilarityScore
from app.repositories.project import ProjectRepo
from app.schemas.compare import CompareResponse
from app.services.project import ProjectService

# Parts of speech to keep: noun and verb (incl. infinitive)
_KEEP_POS = {"NOUN", "VERB", "INFN"}

# Minimum word length after lemmatisation
_MIN_LEN = 4  # > 3 chars

# Simple Russian stop-words (common auxiliaries / pronouns that pass POS filter)
_STOP_LEMMAS = {
    "быть", "стать", "являться", "иметь", "делать",
    "получать", "обеспечивать", "осуществлять",
    "это", "весь", "свой", "который", "такой",
}

_WORD_RE = re.compile(r"[а-яёa-z]+", re.UNICODE | re.IGNORECASE)

_morph = pymorphy3.MorphAnalyzer()


def _extract_lemmas(text: str) -> set[str]:
    """Return a set of significant lemmas from *text*."""
    lemmas: set[str] = set()
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
        if lemma in _STOP_LEMMAS:
            continue
        lemmas.add(lemma)
    return lemmas


def _project_text(project: Project) -> str:
    parts = [
        project.title or "",
        project.problem or "",
        project.goal or "",
        project.expected_result or "",
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

        score = await self._get_score(project_a, project_b)
        keywords = _get_keywords(project_a, project_b)

        return CompareResponse(
            project_a=self.project_service._to_read(project_a),
            project_b=self.project_service._to_read(project_b),
            score=score,
            keywords=keywords,
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
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing.score

        # Compute on-the-fly if both embeddings are present
        if project_a.embedding is not None and project_b.embedding is not None:
            return _cosine_score(project_a.embedding, project_b.embedding)

        return None


def _get_keywords(project_a: Project, project_b: Project) -> list[str]:
    """Return sorted list of common significant lemmas from both projects."""
    text_a = _project_text(project_a)
    text_b = _project_text(project_b)
    if not text_a or not text_b:
        return []
    lemmas_a = _extract_lemmas(text_a)
    lemmas_b = _extract_lemmas(text_b)
    return sorted(lemmas_a & lemmas_b)
