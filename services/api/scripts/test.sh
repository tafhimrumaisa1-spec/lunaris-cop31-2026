#!/usr/bin/env bash
# Full backend suite. Add LUNARIS_TEST_DATABASE_URL=postgresql+psycopg://... for a PostgreSQL run
# (use a throwaway DB: tables are dropped between tests).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] && . .venv/bin/activate
exec python -m pytest "$@"
