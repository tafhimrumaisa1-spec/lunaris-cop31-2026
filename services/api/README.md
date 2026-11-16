# LUNARIS platform API (`services/api`)

FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic. Owner: Agent 05. No frontend code lives here.

**Principle:** nothing is fabricated. If a data source or another agent's package is not bound, the matching
route answers a structured `503 integration_pending` (or an empty list labelled `not_integrated`). It never
returns invented weather, venues, emissions, certifications or impact.

## Quick start

```bash
cd services/api
cp .env.example .env
scripts/dev.sh                       # venv + deps + `alembic upgrade head` + uvicorn on :8000 (SQLite dev fallback)
# or PostgreSQL:
docker compose up --build            # db :5432, api :8000 (runs migrations on start)
```

| Thing | Value |
|---|---|
| API | http://localhost:8000 (`/docs`, `/openapi.json` when `LUNARIS_DOCS_ENABLED`) |
| PostgreSQL (compose) | `localhost:5432`, db/user `lunaris`, password from `.env` `POSTGRES_PASSWORD` |
| Expected web origin (CORS) | `http://localhost:3000` |

## Tests

```bash
scripts/test.sh                                   # everything (SQLite in-memory, one fresh DB per test)
LUNARIS_TEST_DATABASE_URL=postgresql+psycopg://user:pw@localhost:5432/lunaris_test scripts/test.sh   # PostgreSQL (throwaway DB!)
# dependency-free subset (stdlib only: redaction, rate limit, cache, geo, config, provider registry, contract enums):
PYTHONPATH=src:../../packages/contracts python -m unittest discover -s tests/core -t .
```

Suites: `tests/core` (stdlib), `test_contracts.py` (served OpenAPI vs `contracts/openapi-target.yaml`; models vs
`data-models.json`), `test_migrations.py` (Alembic head == models), and endpoint suites with fake providers.
Test DB isolation: every test builds its own app and engine; Postgres runs drop/recreate the schema per test.

## Endpoints

Contract routes (from `contracts/openapi-target.yaml`): `GET /health`, `GET /v1/cities`, `GET|PUT /v1/preferences`,
`GET /v1/weather/dubai`, `POST /v1/heatshield/windows`, `POST /v1/choices/{travel,food,energy}`, `GET /v1/places`,
`GET /v1/business-evidence/{id}`, `GET /v1/missions`, `POST /v1/missions/{id}/interest`, `GET /v1/impact`.

**Additions not in the target contract (need lead sign-off):** `POST|GET|DELETE /v1/session` (guest session),
`DELETE /v1/me` (erase my data). Response bodies for cities/preferences/places/missions/impact are wrapped in
objects (`{"cities": [...]}` etc.) because they must carry status/notice fields.

### Errors

Every error: `{"error": {"code", "message", "request_id", "details": [{"loc","msg","type"}]}}`. Validation errors never echo input.

| Code | HTTP | Meaning |
|---|---|---|
| `validation_error` | 422 | schema violation |
| `session_required` / `invalid_session` | 401 | no / bad / expired / revoked token |
| `rate_limited` | 429 | `Retry-After` header set |
| `request_too_large` / `length_required` | 413 / 411 | body limit; chunked bodies refused |
| `integration_pending` | 503 | no provider bound for this capability |
| `weather_unavailable` | 503 | upstream down and no cache within stale window |
| `provider_contract_violation` | 502 | provider output broke the contract (bad enum, missing evidence, ...) |
| `city_not_supported`, `unknown_city` | 422 | only Dubai is `supported` |
| `comfort_range_required`, `geolocation_consent_required`, `location_outside_city` | 422 | HeatShield input rules |
| `consent_required`, `already_expressed_interest`, `mission_not_accepting_interest` | 422/409/409 | mission interest rules |

## Authentication (read this)

Only **guest sessions** exist: `POST /v1/session` returns an opaque bearer token (HMAC-hashed at rest, 30-day TTL,
revocable). It is a pseudonymous device token, **not a verified identity**, and must not be presented as production
login. **Email auth is not implemented** because no provider/credentials were supplied; `LUNARIS_AUTH_MODE` accepts
only `guest_session`. Deployment TODO: choose a provider, verify its JWTs in `deps.optional_auth`, map `sub` to
`users.id`. Nothing else in the code has to change.

## Provider ports (how other agents plug in)

`lunaris_api/integrations/ports.py` defines sync Protocols: `WeatherProvider`, `ClimateEngine`, `ChoicesEngine`,
`PlacesProvider`, `BusinessEvidenceProvider`, plus `ProviderUnavailable` / `InvalidInput`. Bind with env entrypoints
(`LUNARIS_WEATHER_PROVIDER=pkg.module:Class`, ...). Misconfigured entrypoints fail startup. Providers return plain
dicts matching `data-models.json`; the API re-validates them and answers 502 on violations. Providers must set
their own network timeouts. See `AGENT_05_HANDOFF.md` for the exact method signatures.

## Caching, scheduling, privacy, security

* Weather: fresh cache (default 900 s) -> provider -> stale-if-error (default <= 6 h, response says `state: stale`) -> 503. One upstream call at a time. In-process cache: **single instance only**; multi-instance needs Redis behind `core/cache.py`. Cache only what the provider's licence allows.
* Scheduler: interface only (`core/scheduler.py`); `NullScheduler` refuses registration. **No recurring jobs exist.**
* Geolocation is opt-in (`consent: true`), coarsened to 2 decimals (~1 km), range-checked against the city, held in memory only, never stored or logged.
* Logging: JSON, path only (no query strings), redaction of emails, bearer tokens, long opaque tokens, phones, 3+-decimal coordinates and sensitive keys. Redaction is pattern-based; treat it as defence in depth, not a guarantee.
* CORS: explicit origin allow-list, no credentials, `*` rejected. Body limit 64 KiB default. Rate limits per client IP (read 120/min, write 30/min, session creation 10/h); `X-Forwarded-For` honoured only with `LUNARIS_TRUST_PROXY_HEADERS=true`. Limiter is per process.
* Secrets only via environment; `.env` is git-ignored; production refuses to start without PostgreSQL, a >=32-char secret and HTTPS origins.

## Database

PostgreSQL is the target; SQLite is a **dev/test fallback only** (production config refuses it). Schema via Alembic
(`scripts/migrate.sh`, default `upgrade head`). `LUNARIS_AUTO_CREATE_SCHEMA` (dev default) uses `create_all` + city seed instead.
Cities: Dubai `supported`; Abu Dhabi, London, New York, Singapore `unsupported` (no fake coverage).
The only seeded mission (`LUNARIS_SEED_DEMO_DATA=true`) is titled "DEMO ..." with status `demo`; it has no organizer,
location, date or volunteer count.

## Known limitations

See `AGENT_05_HANDOFF.md` ("Not verified" and "Known failures").
