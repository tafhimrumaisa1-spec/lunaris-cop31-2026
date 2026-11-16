#!/bin/sh
set -eu
alembic upgrade head
exec uvicorn lunaris_api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
