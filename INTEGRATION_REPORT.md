# LUNARIS integration report

Date: 2026-11-15

## Integrated

- The supplied cinematic homepage at `/`, preserving its original Dubai SVG, editorial typography, white outlined location icon, seven-chapter scroll narrative, responsive navigation and reduced-motion fallback.
- The existing functional LUNARIS browser application at `/app/`, with every homepage `.app-link` CTA connected to that route.
- Agent 03 choices and places packages, including their schemas and tests.
- Agent 05 FastAPI service, database models, Alembic migrations, security middleware, guest sessions, Docker and CI assets.
- Handoff contracts from the LUNARIS source bundle.
- A first-party Open-Meteo adapter and a transparent HeatShield comfort-ranking engine.
- A verified choices adapter that exposes Agent 03 calculations and a current DEWA residential electricity estimate.
- The complete responsive web experience, including Lumi, a non-competitive progress trail, sourced calculators, a private browser ledger, and official volunteering routes.

Agent 01 source code was not present in the supplied downloads; only its handoff document was available. The live weather adapter therefore implements the documented interface directly and fails closed when its provider is unavailable.

## Evidence used

- Weather: Open-Meteo Forecast API, Dubai city-centre grid point, `best_match` model selection, CC BY 4.0. The free endpoint has non-commercial terms and published rate limits; commercial deployment must use an appropriate plan.
- Travel: UK Government GHG Conversion Factors for Company Reporting, 2026 revised flat file. These are transparent proxy factors and not Dubai fleet measurements.
- Food: Our World in Data grapher export of Poore & Nemecek (2018), global lifecycle averages. The downloaded CSV is retained in `data/source_cache` with its SHA-256 recorded in the choices source manifest.
- Electricity: DEWA slab tariff page as checked 2026-11-15, including the November 2026 electricity fuel surcharge and 5% VAT. The estimator excludes water, sewerage, housing fees, meter charges and account-specific adjustments.
- Action: Volunteers.ae and the Government of Dubai volunteering guide. LUNARIS makes no event, eligibility or registration claim.

## Verification

- Integrated deterministic suite: 160 passed, 1 opt-in live test skipped, 4 dependency deprecation warnings.
- Opt-in live smoke test: 1 passed. It exercises the real Open-Meteo response through the weather endpoint, HeatShield ranking, and the DEWA API calculation.
- JavaScript syntax check passed.
- Desktop, mobile and onboarding renders were inspected from a local HTTP origin.

## Honest boundaries

- The published static experience uses Open-Meteo directly; the FastAPI service is production-shaped but still requires separate hosting and a managed PostgreSQL database.
- HeatShield ranks personal comfort fit. It is not a medical, occupational-health or physiological safety system.
- Explore is an atmosphere journal, not a live venue directory. No business hours or sustainability claims are presented.
- The impact ledger is a private activity record, not proof of avoided emissions or verified real-world outcomes.
- No email identity provider was supplied, so the API supports guest sessions only.

