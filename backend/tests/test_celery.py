from app.tasks.celery_app import celery, get_embedding_model
from app.tasks.ping import ping


def test_ping_task_returns_pong():
    """ping task should return 'pong' when called directly."""
    result = ping()
    assert result == "pong"


def test_ping_task_registered():
    """ping task should be registered in the Celery app."""
    assert "app.tasks.ping" in celery.tasks


def test_get_embedding_model_returns_none_initially():
    """get_embedding_model should return None before TASK-012 loads the model."""
    assert get_embedding_model() is None


def test_celery_broker_uses_redis():
    """Celery broker and result backend should point to Redis."""
    assert "redis" in celery.conf.broker_url
    assert "redis" in celery.conf.result_backend
