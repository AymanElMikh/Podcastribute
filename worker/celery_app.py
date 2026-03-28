"""Celery application configuration and beat schedule.

All audio processing and LangGraph pipeline execution runs here,
never in FastAPI request handlers.
"""

from celery import Celery

from api.config import settings

celery_app = Celery(
    "podcast_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedule placeholder — periodic tasks added in later phases
celery_app.conf.beat_schedule = {}
