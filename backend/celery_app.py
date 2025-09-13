import os
from celery import Celery
from celery.schedules import crontab

broker = os.getenv("CELERY_BROKER_URL")
backend = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery("tasks", broker=broker, backend=backend)

@celery_app.task(name="tasks.my_task")
def my_task():
    print("Running my scheduled task")

celery_app.conf.beat_schedule = {
    "every-minute-task": {
        "task": "tasks.my_task",
        "schedule": crontab(),
    },
}
celery_app.conf.timezone = "UTC"