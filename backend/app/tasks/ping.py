from app.tasks.celery_app import celery


@celery.task(name="app.tasks.ping")
def ping():
    return "pong"
