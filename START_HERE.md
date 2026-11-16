# LUNARIS — Dubai Launch Candidate

## What you have

A single package containing the original cinematic homepage, consumer demo, Dubai Action Atlas, FastAPI backend, optional experimental ML HeatShield, deployment configuration, and tests.

## Fastest local developer preview

**Terminal 1 (API)**

```bash
cd services/api
python -m venv .venv
# Activate .venv using your shell's method
pip install -r requirements.txt
# macOS/Linux: export PYTHONPATH=src:.
# PowerShell: $env:PYTHONPATH='src;.'
uvicorn lunaris_api.main:app --reload --port 8000
```

**Terminal 2 (web)**

```bash
cd dist
python -m http.server 5173
```

Open http://localhost:5173 — the frontend auto-connects to localhost:8000 when available. For access to built-in weather/provider integrations, configure the provider variables from `services/api/.env.example` in the process environment. Do not assume all features are live without confirming network and provider availability.

## Public pilot deployment

Read `deploy/README.md`. The single-origin Docker Compose arrangement requires PostgreSQL, your own TLS/HTTPS hosting, and production secrets. Hosting is NOT performed by this package. `compose.release.yml` is a starting template to inspect and adapt; it has not been run inside this sandbox.

## Real model evaluation (necessary for a Veritas AI claim)

From the `services/api` directory, with internet access and the correct Python environment:

```bash
PYTHONPATH=src:. python -m ml_training.train --start 2024-07-01 --end 2026-10-31
```

The script must fetch real provider records. Read `ml_docs/MODEL_CARD.md` and the generated evaluation before making any performance claims. The reference data are reanalysis, not independently measured weather stations. If the model fails its validation gate the app must retain the provider forecast. Copy the reviewed `src/artifacts/model.joblib` and `src/artifacts/evaluation.json` to `deploy/models/` for the Compose deployment. Do not claim the model is scientifically validated merely because training finished.

## Real environmental evidence (necessary for Action Atlas detection claims)

Follow `docs/ACTION_ATLAS_INTEGRATION.md` to run the included Earth Engine script using an authorized account. Review cloud masks, export units, seasonality, observation coverage and parcel/privacy limitations. From `services/api`, import the reviewed CSV:

```bash
PYTHONPATH=src:. python scripts/import_atlas_evidence.py YOUR_EXPORT.csv \
  --out ../../deploy/evidence/dubai_area_indicators.json \
  --period 2025-01-01/2025-12-31 \
  --reviewer "Actual reviewer" --ack-reviewed
```

An export of area means is not evidence of individual trees, landowner consent, permitted interventions, or measured cooling benefit. The map always represents approximate neighborhood study areas.

## Verification

```bash
python scripts/preflight.py
cd services/api
PYTHONPATH=src:. pytest -q tests
node --check ../../dist/app/app.js
node --check ../../dist/app/action-atlas/atlas.js
```

Browser/smartphone QA, actual Docker cloud deployment, external data downloads, live accounts, and actual field verification require access to services not available in this environment. Read `RELEASE_NOTES.md` for precise completion boundaries.
