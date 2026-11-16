# LUNARIS Climate Intelligence — Integrated API

The climate engine has been integrated into the **existing FastAPI application**. Original `/v1/heatshield/windows` and `/v1/weather/hourly` endpoints remain unchanged.

## Added endpoints

- `GET /v1/climate-ai/health` — basic state
- `GET /v1/climate-ai/status` — model availability, evaluation scores if trained
- `GET /v1/climate-ai/evaluation` — persisted real evaluation, 404 if not trained
- `POST /v1/heatshield/windows` — **existing** API (takes `city_id`, `activity`, `comfort_min_c`, `comfort_max_c` etc.)
- `POST /v1/heatshield/ai-windows` — **new** API (takes `preferences`, `days`, `limit`); returns labeled forecast method, ranked hours, limitations.

For API disambiguation, new predictive windows are served at `POST /v1/heatshield/ai-windows` and do not replace the original contracts.

## Run locally

From `services/api`, with Python >=3.11 and dependencies installed:

```bash
pip install -r requirements.txt
export PYTHONPATH=src:.
export LUNARIS_AUTO_CREATE_SCHEMA=true
uvicorn lunaris_api.main:app --reload
```

In Windows PowerShell: `$env:PYTHONPATH = 'src;.'`

## Train on historical data (internet required)

```bash
PYTHONPATH=src:. python -m ml_training.train --start 2024-07-01 --end 2026-10-31
```

The training tool fetches historical provider data, trains on chronological dates, saves the test evaluation to `src/artifacts` **unless** `LUNARIS_MODEL_DIR` is provided, and only enables ML correction if validation performance beats raw forecast baseline. Do not call this an improvement without inspecting the real test scores.

Set `LUNARIS_MODEL_DIR` to a persistent directory that is shared between the training job and running API. The default location is `services/api/artifacts` (based on package placement); the saved artifacts must be present on the deployment server. Do not commit pretrained files with unclear data provenance.

## Client integration example

```js
const response = await fetch(`${API_BASE}/v1/heatshield/ai-windows`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({preferences:{min_comfort_c:20,max_comfort_c:30,prefers_clouds:true,activity:'walking'},days:2,limit:6})
});
if(!response.ok) throw new Error(`Climate API ${response.status}`);
const result = await response.json();
// If result.ml_status === 'not_trained', display Open-Meteo attribution, not an AI accuracy claim.
```

The historical training reference is reanalysis, NOT independent station observations. No real-world health safety guarantees, neighborhood resolution, or user-level comfort validation are claimed.
