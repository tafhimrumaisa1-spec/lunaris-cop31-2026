#!/usr/bin/env bash
# Local dev server on http://localhost:8000 using the SQLite dev fallback (or LUNARIS_DATABASE_URL).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements-dev.txt
[ -f .env ] && set -a && . ./.env && set +a
alembic upgrade head
exec uvicorn lunaris_api.main:app --reload --host 127.0.0.1 --port "${PORT:-8000}"
