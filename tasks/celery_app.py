from celery import Celery

from config import settings

celery_app = Celery(
    "email_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.email_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
