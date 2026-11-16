# LUNARIS Action — Dubai City Opportunity Atlas

## Status and scope
This working module is an **exploratory, research-stage city atlas**, not a verified site recommendation system. It has 12 illustrative area-level concepts across Dubai, real approximate neighborhood locations, six environmental themes, a scenario calculator, evidence references and a **consent-based interest ledger**. Nothing claims to be field-verified, approved, or the output of a trained AI model.

### Why it is useful now
- Shows the entire first city pilot with map filters for greenery, biodiversity, cooling, water, waste and clean energy.
- Lets visitors inspect a potential action, missing verification steps, linked Dubai policy objective and relevant SDGs.
- Calculates an adjustable hypothetical outcome (canopy footprint, shade footprint, potential generation, diversion, etc.) and a budget scenario. Estimates are **not environmental predictions**. They are NOT proof of improvement.
- Allows users to record their interest on a guest session when the LUNARIS API is online. No real volunteer place, event or organizer is implied. The fallback saves intent only in local browser storage.
- Downloads a plain-text evidence / assumption brief for each concept.

## Files
- `dist/app/action-atlas/index.html`, `atlas.css`, `atlas.js`: standalone interactive UI.
- `services/api/src/lunaris_api/action_atlas/catalog.py`: all illustrative area proposals and policy mapping.
- `services/api/src/lunaris_api/action_atlas/scenario.py`: deterministic, bounded scenario arithmetic.
- `services/api/src/lunaris_api/action_atlas/export_gee.js`: Earth Engine workflow for obtaining *real area-level land-cover / surface-temperature indicators* (not automatically run).
- `services/api/src/lunaris_api/routers/action_atlas.py`: API endpoints.
- `services/api/src/lunaris_api/app.py`: additive router registration.
- `services/api/tests/test_action_atlas.py`: scenario and endpoint tests.
- `dist/app/index.html`: links into the new module from the existing Action page.

## API routes
- `GET /v1/action/atlas` → area catalogue, clear evidence status, scenario defaults.
- `POST /v1/action/atlas/{area_id}/scenario` → hypothetical scenario calculator (not ML).
- `POST /v1/action/atlas/{area_id}/interest` → explicit consent and authenticated guest-session required; records concept-only interest in existing `missions` and `mission_interests` tables. Returns a notice that no real event exists.

No additional migrations required; uses existing schema.

## Local test
```bash
cd services/api
PYTHONPATH=src:. pytest -q tests/test_action_atlas.py
PYTHONPATH=src:. pytest -q tests
node --check ../../dist/app/action-atlas/atlas.js
cd ../../dist && python -m http.server 5173
```
Navigate to `/app/` → Action → **Open Dubai Opportunity Atlas**. Start API on port 8000 as explained in `README_INTEGRATED.md`.

## Satellite-data workflow — next evidence gate
1. Visit https://code.earthengine.google.com with a valid Earth Engine account and run `export_gee.js`.
2. Inspect and document the season, temporal baseline, data masking, observation counts, coverage and sensor resolution.
3. Export the indicator CSV. **Do not label the conceptual opportunity records as 'satellite detected' until the actual results have been reviewed and locally matched.**
4. Apply scientifically defensible ranking / uncertainty treatment. Ground shade interventions in pedestrian/access surveys, planting proposals in utilities and irrigation analysis, PV in roof/utility checks and water measures in measured baselines.
5. Future ML work must train on ground-truth targets (e.g. held-out surface-temperature observations or verified heat exposure), with spatially and temporally held-out validation. The current Atlas is **not** trained machine learning.

## Policy sources and interpretation
- [Dubai 2040 Urban Master Plan](https://www.dm.gov.ae/municipality-business/planning-and-construction/dubai-2040-urban-master-plan/): better accessibility, open spaces and environmental quality.
- [Greenery and Plantation Manual 2026](https://www.dm.gov.ae/greenery-and-plantation-manual-2026-launched/): biodiversity, local ecology, irrigation and long-term stewardship.
- [Blue and Green Spaces Roadmap 2030](https://www.dm.gov.ae/mohammed-bin-rashid-reviews-blue-and-green-spaces-roadmap-2030/): area-wide public realm and nature objectives.
- [Dubai Demand Side Management Strategy 2050](https://dubaisce.gov.ae/en/dsmstrategy2050/): water and energy efficiency.
- [Dubai Clean Energy Strategy](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/environment-and-energy/dubai-clean-energy-strategy): clean energy transition.
- [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1): 10 m land-cover class probability data.

**Important:** Dubai 2040's 60% land area for nature reserves and rural natural areas refers to the **whole emirate**, not to an achievable 60% canopy cover in urban Dubai. A specific candidate neighborhood is not evidence of unused public land.

## Deployment requirements
- Leaflet and OpenStreetMap tiles currently load via CDNs; browser requires network access. Offline fallback provides a schematic pin map.
- OSM standard tiles are acceptable for limited, attributed prototypes; commercial/large-scale use needs compliant tile hosting/provider.
- Use the existing LUNARIS backend. A separate static deployment requires the backend CORS allowlist and `LUNARIS_API_BASE` configured.
- Guest sessions are not production authentication; replace with consented persistent accounts before live volunteer recruitment.
- Protect candidate sites and sensitive ecological areas; do not publicly publish precise sensitive species/habitat coordinates.
- Before allowing real user-generated missions, implement partner vetting, moderation, privacy controls, abuse protection, age-appropriate safeguards, approvals and status audits.
