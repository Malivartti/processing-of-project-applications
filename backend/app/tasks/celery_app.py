from celery import Celery
from celery.signals import worker_init

from app.config import settings

celery = Celery(
    "ppa",
    broker=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    include=["app.tasks.ping", "app.tasks.embeddings"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Global placeholder for the embedding model (populated in TASK-012)
_embedding_model = None


def get_embedding_model():
    """Return the loaded embedding model. Populated via worker_init signal."""
    return _embedding_model


@worker_init.connect
def load_models(sender, **kwargs):
    """Load rubert-tiny2 at worker startup (once per process)."""
    global _embedding_model
    from app.services.embedding import load_sentence_transformer

    _embedding_model = load_sentence_transformer()
