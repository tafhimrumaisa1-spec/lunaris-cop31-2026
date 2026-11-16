# LUNARIS Dubai — Launch Candidate (NOT DEPLOYED)

This is an implementation-ready source archive, not a live website. The automated tests exercise backend behavior and JS syntax; browser navigation to localhost was blocked in the current sandbox.

## Completed in this handoff (priority order)

1. **Deployment infrastructure (P0)** — Single-origin frontend and API via nginx, PostgreSQL-backed API, migration-on-startup, Docker Compose sample, explicit HTTPS/public-origin settings. Docker runtime and actual cloud deployment were not available here.
2. **Climate Engine consistency (P0)** — Preserved existing experimental ML correction and 24-hour validation-gated inference, third-party forecast fallbacks and model-status endpoints. Added startup documentation and checks for the actual reviewed artifact. A trained model is NOT available in this archive. Internet was blocked for fetching Open-Meteo archives.
3. **Optional session preferences (P1)** — Browser onboarding continues offline, and now attempts to sync to the established guest session API (same temporary token used by Action Atlas). Guest sessions are not verified cross-device accounts; notification consent remains false.
4. **Action Atlas reviewed evidence pipeline (P1)** — A strict import script validates a manually reviewed Earth Engine CSV export; `/v1/action/atlas/evidence` responds with documented area-level indicators only when available. The Atlas displays these in an explicit evidence section, separate from proposed actions and hypothetical scenario benefits. No satellite CSV or detection claims are fabricated.
5. **Privacy control (P1)** — Added an explicit erase-data action to the Impact area that removes browser records and attempts `/v1/me` guest-account deletion; if the backend is unavailable it retains the session token for a future retry.
6. **Regression tests and static checks** — Added four tests covering no-evidence, invalid measurements, valid reviewed data, and endpoint response. Existing frontend preserved. All documented simulation caveats retained.

## External blockers before a real public launch

- Host the single-origin site on an HTTPS-enabled platform and configure **your own credentials**, public origin, environment variables and backups. Run browser QA and check live URLs externally.
- Download real historical Dubai weather forecast and reanalysis data, execute `ml_training.train`, review model failures/baselines and activate only models that pass the validation gate. Models use a reanalysis reference, not station truth.
- Run the Earth Engine script with an approved account, review imagery/cloud masking and temporal scope, export CSV, then import with the evidence script. No site-verified planting or temperature reductions can be claimed without field review.
- Confirm API data-source licensing and commercial usage (including Open-Meteo and OSM), privacy notice, user-data deletion and partner vetting before broad public rollout.
- Full social features, uploads, certified green businesses, property-level risk, authentic volunteer opportunities, and external account identity are **not implemented**. These remain scoped extensions, not hidden claims.

## What to check in your browser

- Homepage scroll narrative, mobile performance and the `/app` CTA
- Onboarding save and optional guest sync when backend online
- Dubai weather and HeatShield source/method labels when upstream online/offline
- Choice calculators source notes, non-Dubai proxy factor disclosures
- Action Atlas filters, case scenarios, evidence panel, Join-interest consent, private-data handling
- HTTPS, route refreshes, no JS console exceptions, keyboard access, mobile viewport

## Next actions

Use `python scripts/preflight.py`, then read `deploy/README.md`. This handoff does not include credentials or any live deployment URL.
# COP31 v8 final production release

- Preserved the supplied ten-step `/tour/` walkthrough and all COP31 routes.
- Added secure server-side Groq conversation for Lumi with an explicit
  read-only tool allowlist and a bounded, clearly labelled local fallback.
- Added the validated NASA POWER 2024–2025 Dubai snapshot: 731 complete days,
  zero missing days, and transparent previous-day/prior-year baseline errors.
- Fixed the HeatShield exposure-setting regression inherited from the package.
- Added an independent Vercel configuration; the frozen Veritas repository and
  deployment are not connected to this release.
