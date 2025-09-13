#!/bin/sh

export MODULE_NAME="main"
export VARIABLE_NAME="app"
export HOST="0.0.0.0"
export PORT=8000


if [ "$UVICORN_RELOAD" = "true" ]; then
    uvicorn $MODULE_NAME:$VARIABLE_NAME --host $HOST --port $PORT --reload --reload-dir /app --reload-include '*.*'
else
    uvicorn $MODULE_NAME:$VARIABLE_NAME --host $HOST --port $PORT
fi