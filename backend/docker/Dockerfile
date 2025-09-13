FROM python:3.12-slim-bookworm

WORKDIR /app

COPY . .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

RUN chmod +x ./docker/entrypoint-api.sh
RUN chmod +x ./docker/entrypoint-celery-worker.sh
RUN chmod +x ./docker/entrypoint-celery-beat.sh