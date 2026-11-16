#!/usr/bin/env bash
# Generate a fully pinned lock (needs network). Commit requirements.lock and install from it in CI/prod.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -q pip-tools
pip-compile --generate-hashes -o requirements.lock requirements.txt
