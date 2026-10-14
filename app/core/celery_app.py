from celery import Celery
from app.core.config import settings


app = Celery('app', broker=settings.redis_url, backend=settings.redis_url)

app.conf.beat_schedule = {
    "fetch-prices-async": {
        "task": "fetch_prices",
        "schedule": 60.0,
    },
}

app.autodiscover_tasks(["app.tasks"])
