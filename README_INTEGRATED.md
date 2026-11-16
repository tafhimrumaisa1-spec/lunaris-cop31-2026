# LUNARIS — Climate AI Integrated Edition

This is the user-supplied LUNARIS app with the previous Climate Intelligence Engine merged into the **existing FastAPI backend**, plus an optional consumer HeatShield UI connection.

## What changed
- `services/api/src/lunaris_climate/`: ML modeling, forecast-source clients and recommendation service
- `services/api/ml_training/`: CLI to train and evaluate with real Dubai historical data
- `services/api/src/lunaris_api/app.py`: registered the additional AI router
- `services/api/requirements.txt`: declared climate engine dependencies
- `services/api/tests/test_climate_ai_integration.py`: integration tests
- `services/api/tests/test_climate_standalone.py`: standalone ML tests adjusted to avoid colliding with original endpoint
- `dist/app/app.js`: optional AI API consumption, explicitly labeled rule/provider fallback
- `dist/app/config.js`: API origin configuration
- `dist/app/index.html` and `dist/app/styles.css`: AI status disclosure

## Run backend
From `services/api`:
```bash
pip install -r requirements.txt
PYTHONPATH=src:. uvicorn lunaris_api.main:app --reload --port 8000
```
On PowerShell, set `$env:PYTHONPATH = 'src;.'` before calling uvicorn.

To activate the original provider endpoints, set `LUNARIS_WEATHER_PROVIDER=lunaris_api.integrations.builtin:OpenMeteoWeatherProvider` and `LUNARIS_CLIMATE_ENGINE=lunaris_api.integrations.builtin:ComfortWindowEngine`. Read `.env.example` for other options. Set CORS origins to the static frontend origin.

## Run the bundled static frontend
From the `dist/` folder:
```bash
python -m http.server 5173
```
Open `http://localhost:5173/` and follow the Try Platform route (`/app/`).
`dist/app/config.js` defaults to `http://localhost:8000` on localhost and to same origin otherwise. When deploying statically on a separate production domain, change it to the full public API origin, and set the corresponding backend CORS allowlist.

## Train the real experiment
From `services/api`, with network access:
```bash
PYTHONPATH=src:. python -m ml_training.train --start 2024-07-01 --end 2026-10-31
```

The default training artifacts live under `services/api/src/artifacts`. Set `LUNARIS_MODEL_DIR` on both trainer and server to a persistent directory when deployed. **No real trained model is bundled.** The frontend continues using source-attributed Open-Meteo forecasts and transparent preference ranking until a trained model passes the validation gate. Read `services/api/ml_docs/INTEGRATION.md` for endpoints.

## Tests
```bash
cd services/api
PYTHONPATH=src:. pytest -q tests
node --check ../../dist/app/app.js
```

## Scope
This ZIP includes the existing published static UI and backend source. It does **not** include the original editable frontend source tree, because that source was not present in the uploaded ZIP; the provided frontend was built into `dist/`. Codex can migrate the existing static bundle into a maintainable frontend project if desired.

No external deployment occurred, and provider API availability could not be evaluated in the sandbox. Model scores must be reported only after actual historical data training and held-out evaluation.

## NEW: Dubai City Opportunity Atlas
From the consumer app, choose **Action → Open Dubai Opportunity Atlas** (`/app/action-atlas/`).
Includes 12 area-level proposal concepts across six environmental themes, live OSM map with fallback, policy-aligned goals, hypothetical impact scenario calculations, proposal briefs and consented demo interest recording. See `docs/ACTION_ATLAS_INTEGRATION.md`. The concepts are not yet satellite-verified or municipally approved; see Earth Engine export script and evidence gates.
