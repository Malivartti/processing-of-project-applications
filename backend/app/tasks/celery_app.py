import os

from celery import Celery

celery = Celery(
    "ppa",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    result_backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=["app.tasks.ping"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


def get_embedding_model():
    """Placeholder for ML model - will be implemented in TASK-012."""
    return None
