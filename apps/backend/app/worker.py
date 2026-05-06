from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "o1agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.timezone = "America/Los_Angeles"
celery_app.conf.beat_schedule = {
    "discover-speaking-ops": {
        "task": "app.tasks.discover_speaking_ops",
        "schedule": crontab(hour=16, minute=0, day_of_week="friday"),  # Fridays 4pm PT
    },
    "discover-membership-ops": {
        "task": "app.tasks.discover_membership_ops",
        "schedule": crontab(hour=9, minute=0, day_of_month="1"),  # 1st of each month, 9am PT
    },
    "discover-media-ops": {
        "task": "app.tasks.discover_media_ops",
        "schedule": crontab(hour=9, minute=0, day_of_week="wednesday"),  # Wednesdays 9am PT
    },
    "discover-judging-ops": {
        "task": "app.tasks.discover_judging_ops",
        "schedule": crontab(hour=9, minute=0, day_of_week="tuesday"),  # Tuesdays 9am PT
    },
    "discover-publishing-ops": {
        "task": "app.tasks.discover_publishing_ops",
        "schedule": crontab(hour=9, minute=0, day_of_week="thursday"),  # Thursdays 9am PT
    },
    "poll-outcomes": {
        "task": "app.tasks.poll_outcomes",
        "schedule": crontab(hour=17, minute=0),  # Daily 5pm PT
    },
}
celery_app.autodiscover_tasks(["app"])


@celery_app.task(name="app.tasks.health_check")
def health_check():
    return {"status": "ok"}
