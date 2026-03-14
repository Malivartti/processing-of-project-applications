from celery import Celery
from celery.signals import worker_init

from app.config import settings

celery = Celery(
    "ppa",
    broker=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    include=["app.tasks.ping"],
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
    """Load ML models when the Celery worker starts.

    The actual model (rubert-tiny2) will be loaded in TASK-012.
    This hook is called once per worker process before tasks begin.
    """
    global _embedding_model
    # Placeholder: TASK-012 will assign the real SentenceTransformer here
    _embedding_model = None
