#!/bin/sh

if [ "$UVICORN_RELOAD" = "true" ]; then
    watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- \
    celery -A "$CELERY_APP" beat --loglevel="$LOGLEVEL"
else
    celery -A "$CELERY_APP" beat --loglevel="$LOGLEVEL"
fi