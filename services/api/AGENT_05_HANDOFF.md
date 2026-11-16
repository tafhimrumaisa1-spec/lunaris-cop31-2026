# AGENT 05 HANDOFF — platform API

## 1. Verification status (read first)

The build sandbox had **no network and no FastAPI, Pydantic, SQLAlchemy, Alembic, httpx or pytest installed**,
so most of this service has **never been executed**.

| Area | Status |
|---|---|
| `core/*`, `config.py`, `enums.py`, `integrations/*`, `lunaris_contracts` | **Executed.** 34 stdlib `unittest` tests pass (`python -m unittest discover -s tests/core -t .`). Includes enum drift check against `contracts/data-models.json`. |
| Everything importing fastapi / pydantic / sqlalchemy / alembic (`app.py`, `routers/*`, `services/*`, `schemas.py`, `db/*`, `middleware.py`, `alembic/*`) | **Compiled (`py_compile`) and statically checked** (custom AST pass: no undefined names, all intra-package imports resolve). **Not run.** |
| `tests/test_*.py` (endpoint, contract, migration suites) | **Written, never run.** They are expected to need small fixes on first run. |
| Docker / compose / CI workflow | Syntax-checked only (`bash -n`, YAML parse). Never built or run. |
| PostgreSQL | Never exercised; SQLite-specific behaviour was also never exercised. |
| Dependency lock | Not generated (needs network): `scripts/lock.sh`. Ranges are in `requirements.txt`. |

**First action for whoever has network:** `cd services/api && pip install -r requirements-dev.txt && python -m pytest`, then fix what breaks. Please do not treat the API as working until that is green.

## 2. Ports and commands

* API `:8000` (matches `servers:` in the target contract). PostgreSQL (compose) `:5432`. Web origin allowed by CORS: `:3000`.
* Dev: `cd services/api && cp .env.example .env && scripts/dev.sh`
* Compose: `docker compose up --build` (needs `POSTGRES_PASSWORD` in `.env`)
* Migrate: `scripts/migrate.sh` (= `alembic upgrade head`); migrations: `0001_initial` (schema + 5-city registry). **Pending migrations: none.**
* Tests: `scripts/test.sh` (SQLite) / `LUNARIS_TEST_DATABASE_URL=... scripts/test.sh` (Postgres)
* Dump served OpenAPI for diffing: `PYTHONPATH=src python scripts/export_openapi.py > served-openapi.json`

## 3. Integration interface (for Agents 01-04)

Bind via env `module:attr` (class, factory or instance). All methods **sync**; set your own HTTP timeouts. Return plain dicts shaped like `contracts/data-models.json`. Raise `ProviderUnavailable` for outages, `InvalidInput` (message safe to show) for bad user input (both from `lunaris_api.integrations.ports`; they are plain exceptions, import-free of FastAPI).

| Env var | Method | Notes |
|---|---|---|
| `LUNARIS_WEATHER_PROVIDER` | `fetch_hourly(*, city_id, latitude, longitude, timezone, hours) -> list[HourConditions]` | ascending timestamps; every hour carries `Evidence`; allowed `data_status`: live/historical/modeled/demo. Return >= `hours` entries if possible. |
| `LUNARIS_CLIMATE_ENGINE` | `rank_windows(*, hours: list[dict], params: dict) -> list[ActivityWindow]` | params: `activity, window_minutes, max_windows, comfort_min_c, comfort_max_c, location (coarse|None)`. Unique `comfort_rank`; `heat_caution` in low/moderate/elevated/unknown; allowed `data_status`: live/modeled/demo. |
| `LUNARIS_CHOICES_ENGINE` | `compare(*, kind, payload) -> ChoiceComparison` | `kind` in travel/food/energy. **Engine owns all domain validation** (payload field names are not fixed by any contract); API only checks JSON envelope (depth, size, NaN). Result must have >=1 Evidence, `comparison_type == kind`, no `verified`/`self_reported`. |
| `LUNARIS_PLACES_PROVIDER` | `list_places(*, city_id, category, limit) -> list[dict]` | needs `id, name, data_status, evidence[>=1]`; extra keys pass through. |
| `LUNARIS_BUSINESS_EVIDENCE_PROVIDER` | `get_profile(business_id) -> dict|None` | needs `id, disclosure_status in {self_reported, documentation_reviewed}, evidence[>=1]`. `independently_verified` is rejected (MVP). |

**Currently none of these are bound**, because no downstream package existed when I built this. Consequences today:
`/v1/weather/dubai`, `/v1/heatshield/windows`, `/v1/choices/*`, `/v1/business-evidence/{id}` return `503 integration_pending`;
`/v1/places` returns `[]` with `source_status.state = "not_integrated"`. Working without any binding: `/health`, `/v1/cities`, sessions, preferences, missions (+ interest), impact.
**So the P0 "live weather -> HeatShield" journey is not delivered until Agents 02/03 supply the weather provider and climate engine.** I deliberately did not write an Open-Meteo client here (it belongs to the data-adapter package and I could not test one without network).

## 4. Contract gaps and ambiguities found (needs lead decision)

1. **`HourConditions` is strict (`extra=forbid`).** DATA_AND_EVIDENCE.md lists wind, cloud cover, precipitation amount, UV, but `data-models.json` has no such fields. A provider that emits them will get `502 provider_contract_violation`. Either extend the contract or providers must drop them.
2. **`Evidence` lacks provenance fields** that DATA_AND_EVIDENCE.md requires (`license_note, location_precision, model_id, assumptions, uncertainty`). I added them as **optional** fields. Contract should adopt (or reject) them.
3. **`Evidence.data_status` mixes two ideas**: data origin (live/historical/modeled/demo) and record-review state (self_reported/verified). To stop forecasts or estimates claiming `verified`, the API enforces per-surface allow-lists (`enums.py`): weather live/historical/modeled/demo; windows live/modeled/demo; choices live/historical/modeled/demo. Violations -> 502.
4. **Three incompatible verification vocabularies**: mission `unverified|self_reported|reviewed|verified`; impact `self_reported|reviewed|verified`; business disclosure (DATA_AND_EVIDENCE #11) `self_reported|documentation_reviewed|independently_verified`, which exists in no contract. I implemented business disclosure as a separate enum and flagged it; `tests/core/test_contract_enums.py` will fail if the contract ever absorbs it.
5. `ChoiceComparison.comparison_type` includes `business`, but there is no `/v1/choices/business` route and `/v1/business-evidence/{id}` returns an "evidence profile", not a ChoiceComparison. Its schema is therefore only loosely typed (`id`, `disclosure_status`, `evidence`, extras allowed).
6. **No way to create impact records.** The target has only `GET /v1/impact`. The table, model, and read path exist (with a DB CHECK that blocks invalid statuses), but with no `POST` the ledger is always empty. Needs a contract decision (who may write, and how `reviewed`/`verified` get set; users must only ever create `self_reported`).
7. Preference vocabularies were inferred from PRODUCT_BRIEF journey 2 and are **enforced**: moods `rainy_cozy, cloudy_moody, sunny, breezy, misty, after_dark`; activities `cafes, walking, exercise, culture, indoor` (`enums.py`). Codex must use exactly these slugs or tell me the real list. `priorities` is a free slug list.
8. Routes I added beyond the target: `POST|GET|DELETE /v1/session`, `DELETE /v1/me`. List/GET bodies are wrapped objects (see README). `openapi-target.yaml` should be updated to match; `tests/test_contracts.py` only checks that target paths/methods/status codes are a subset of what is served.

## 5. Behaviour decisions worth knowing

* Preferences: `GET` with no session or nothing saved -> `preferences: null` (no invented defaults; the 19-29 °C in the demo script is a user pick, not a default). Saving for an `unsupported` city is refused; `preview` would be allowed but no city is currently `preview`.
* HeatShield: comfort range comes from the request or saved preferences, else 422. Response always includes `notices` stating comfort != safety. The API never emits the word "safe".
* Weather outage: serves stale cache up to `LUNARIS_WEATHER_STALE_MAX_SECONDS` flagged `state: stale` with the original `retrieved_at` untouched; otherwise 503.
* Mission interest: needs session + `consent: true`; accepted only for `demo` missions or `approved/active` missions with `permission_status=approved`; response always has `registration_confirmed: false`; audit row written; one interest per user per mission (409 after). No free-text field is accepted (PII/abuse surface).
* `DELETE /v1/me` erases user, sessions, preferences, interests, impact records; audit rows are kept with the actor nulled.

## 6. Known failures / limitations

* Everything in section 1 marked not run.
* Rate limiter and weather cache are in-process: wrong for multi-instance deployments; shared store needed.
* `X-Forwarded-For` handling takes the right-most entry (assumes exactly one trusted proxy).
* Redaction is regex-based; it will also redact some innocuous 4+-decimal numbers in log text.
* The `Authorization` header with a non-Bearer scheme is ignored (treated as no credentials).
* The 411 rule for chunked uploads is intentional; clients must send `Content-Length`.
* No email auth, no scheduler backend, no recurring jobs, no push/notification delivery (consent is stored, nothing is sent).
* `Settings.for_tests` is public API for tests only.
* `packages/contracts` currently ships only a Python loader (`lunaris_contracts`); I did **not** generate JSON Schemas from the Pydantic models (needs a runnable env).

## 7. Files I own / created

`services/api/**`, `packages/contracts/**` (Python loader only), `.github/workflows/api-ci.yml`. I read `contracts/*` and modified nothing there.
