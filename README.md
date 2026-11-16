# LUNARIS COP31

LUNARIS is a Dubai-first climate intelligence and action platform connecting
personal heat adaptation, lower-impact everyday choices, and city-scale
environmental opportunity. This repository is the independent COP31 release;
it is not the frozen Veritas AI Hackathon repository.

## Product routes

- `/` — cinematic public story and three intelligence layers
- `/tour/` — accessible ten-step guided walkthrough
- `/app/` — consumer platform with HeatShield, Explore, Choices, Lumi and Impact
- `/app/action-atlas/` — conceptual Dubai neighborhood opportunities
- `/app/action-atlas/dubai-heat-case/` — sourced Dubai heat case and NASA POWER snapshot
- `/app/cop31-lab/` — transparent intervention scenario lab
- `/app/foodprint-fridge/` — Fridge Brain
- `/app/home-resilience/` — household resilience self-check
- `/app/wallet/` — Carbon & Cost Wallet
- `/app/insurance/` — climate insurance education guide

All Action Atlas opportunities remain concepts, not approved projects,
satellite-verified sites, confirmed volunteer events or measured impact.

## Lumi

The seventh app dock item opens Lumi's session-only conversation view. The
browser sends bounded history to the same-origin Vercel function at
`/api/lumi`; `GROQ_API_KEY` never enters `dist/` or a browser response.

The server exposes only an explicit read-only tool allowlist:

- Open-Meteo Dubai weather and transparent HeatShield window comparison
- sourced GreenMiles travel factors
- existing DEWA electricity-component scenario logic
- the conceptual Action Atlas catalogue
- the reviewed Explore venue catalogue
- Open Food Facts product identity lookup
- the bundled NASA POWER snapshot status and baseline metrics

If Groq or a provider is unavailable, the interface labels the failure and
uses the bounded local guide. Lumi is not a medical, emergency, legal,
insurance or professional safety authority.

### Required Vercel variables

Set these in the new COP31 Vercel project's Production, Preview and Development
environments, then redeploy:

- `GROQ_API_KEY` — your Groq secret
- `GROQ_MODEL` — a current tool-capable model; this release defaults to
  `openai/gpt-oss-20b`

Never prefix the key with `PUBLIC_` or place it in frontend files. The endpoint
bounds input, history and output; validates same-origin browser requests; uses
provider timeouts; and includes a best-effort per-instance limiter. Add a
distributed Vercel Firewall rate limit for `/api/lumi` before high-traffic use.

## NASA POWER snapshot

`research/dubai_heat_case.py` downloaded and validated 731 complete daily NASA
POWER records for 2024–2025 at the documented Dubai reference coordinate. The
committed artifact reports:

- 2024 June–August mean daily maximum: **34.7192°C**
- 2025 June–August mean daily maximum: **34.0382°C**
- 2025 previous-day baseline MAE: **0.8554°C**
- 2025 prior-year-day baseline MAE: **1.3702°C**
- 92 matched evaluation days and zero missing days

These are coarse gridded/reanalysis-derived two-metre atmospheric estimates,
not station observations, satellite land-surface temperature, neighborhood
heat-island validation or an intervention-impact result. Neither baseline is
an AI model.

Reproduce the artifact with internet access:

```powershell
python research\dubai_heat_case.py --output dist\app\action-atlas\dubai-heat-case\nasa_power_metrics.json
```

## Local preview

```powershell
python -m http.server 8791 --directory dist
```

Open `http://127.0.0.1:8791/`. The static server exercises the local Lumi
fallback; run through Vercel to exercise `/api/lumi`.

## Tests

```powershell
python -m pytest -q services\api\tests packages\choices\tests packages\places\tests research -p no:cacheprovider
node --check dist\app\app.js
node --check dist\tour\tour.js
node tests\cop31_lab_dom_smoke.cjs
```

The live-provider test is intentionally skipped unless explicitly enabled.

## Deployment

Import this repository into a **new** Vercel project. Leave Root Directory at
the repository root, choose the Other preset, and do not add a frontend build
command. `vercel.json` publishes `dist/` and deploys `api/lumi.py` as a Python
Function. Do not connect this repository or project to the Veritas deployment.

The full FastAPI/PostgreSQL service remains available under `services/api` but
is not mounted by this Vercel project. Persistent guest accounts and server-side
Action interest therefore require a separately hosted backend; current static
pages preserve labelled local-only fallback behavior.

## Licensing and provenance

Code is Apache-2.0 except where stated. The LUNARIS name, Lumi mascot, visual
identity and supplied media are excluded from that code license; see
[BRAND.md](BRAND.md) and [NOTICE](NOTICE). Preserve the Git history and disclose
pre-existing work accurately in any COP31 submission.
