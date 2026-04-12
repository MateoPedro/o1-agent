from celery import Celery
from app.config import settings

celery_app = Celery(
    "o1agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "discover-speaking-ops": {
        "task": "app.tasks.discover_speaking_ops",
        "schedule": 86400.0,  # daily
    },
    "poll-outcomes": {
        "task": "app.tasks.poll_outcomes",
        "schedule": 3600.0,  # hourly
    },
}
celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app"])


@celery_app.task(name="app.tasks.health_check")
def health_check():
    return {"status": "ok"}
