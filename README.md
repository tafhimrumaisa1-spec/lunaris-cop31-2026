**Latest build:** See [FINAL_V3_TEST_GUIDE.md](FINAL_V3_TEST_GUIDE.md) for the v3.1 consumer intelligence implementation, sources, checks and limitations.

# LUNARIS

LUNARIS is a Dubai-first, evidence-aware city companion. The browser experience combines live Open-Meteo conditions, personal comfort-window ranking, sourced travel and food comparisons, a current DEWA electricity estimator, and links to official volunteering platforms.

The public `/` route is the supplied cinematic LUNARIS homepage. The functional product is preserved at `/app/`. All homepage CTAs use the shared `.app-link` contract and resolve to `/app/`.

## Run the site

```powershell
python -m http.server 8791 --directory dist
```

Then open `http://127.0.0.1:8791` for the homepage or `http://127.0.0.1:8791/app/` for the application.

The static site makes its weather request directly to Open-Meteo. All preferences, Lumi trail progress, and impact-ledger entries stay in the browser's local storage.

## Run the API

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r services\api\requirements-dev.txt
.\services\api\scripts\dev.ps1
```

The built-in adapters are configured in `services/api/.env.example`. PostgreSQL is required in production; SQLite is a development fallback.

## Verify

```powershell
.\.venv\Scripts\python -m pytest -q services\api\tests packages\choices\tests packages\places\tests -p no:cacheprovider
$env:LUNARIS_LIVE='1'
.\.venv\Scripts\python -m pytest -q services\api\tests\test_live_builtin.py -p no:cacheprovider
```

See [INTEGRATION_REPORT.md](./INTEGRATION_REPORT.md) for provenance, integrated agent work, and remaining deployment boundaries.

