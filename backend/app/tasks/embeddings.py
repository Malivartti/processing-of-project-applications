from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Project
from app.services.embedding import EmbeddingService
from app.tasks.celery_app import celery, get_embedding_model
from app.utils.text import TextProcessingUtils


def _get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery.task(name="app.tasks.embeddings.bulk_generate_embeddings")
def bulk_generate_embeddings(project_ids: list[str]) -> dict:
    """Compute and store embeddings for the given project IDs.

    Uses the rubert-tiny2 model loaded at worker startup.
    Skips projects that already have an embedding.
    """
    model = get_embedding_model()
    if model is None:
        return {"skipped": len(project_ids), "reason": "model_not_loaded"}

    uuids = [uuid.UUID(pid) for pid in project_ids]

    with _get_sync_session() as session:
        projects: list[Project] = (
            session.execute(
                sa.select(Project).where(
                    Project.id.in_(uuids),
                    Project.embedding.is_(None),
                )
            )
            .scalars()
            .all()
        )

        if not projects:
            return {"processed": 0}

        svc = EmbeddingService(model)
        texts = [
            TextProcessingUtils.prepare_text(
                p.title, p.problem, p.goal, p.expected_result
            )
            for p in projects
        ]
        vectors = svc.encode(texts)

        for project, vector in zip(projects, vectors):
            project.embedding = vector.tolist()

        session.commit()

    return {"processed": len(projects)}
