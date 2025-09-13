from fastapi.testclient import TestClient

from celery.result import AsyncResult
from celery_app import my_task, celery_app  # adjust import if needed

from .main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

def test_celery_task_runs():
    result: AsyncResult = my_task.delay()

    completed = result.get(timeout=10)

    assert result.successful(), f"Task failed with state {result.state}"