# LUNARIS COP31 v4.0 — Action & Resilience Lab

## Included
- Full v3.3 LUNARIS baseline, including Dubai Opportunity Atlas, existing app calculators, Lumi bounded local guide, FastAPI project and deployment files.
- New standalone mobile-responsive `dist/app/cop31-lab/` with `index.html`, `lab.css` and `lab.js`.
- Public homepage summary upgraded to eight experiences, with explicit LUNARIS Action and Lumi tiles.
- Public homepage COP31 spotlight links to the lab.
- In-app home COP31 feature links to the lab.

## What works immediately, entirely client-side
1. A five-step interactive product tour with links into existing project surfaces.
2. Editable 200 m pedestrian corridor scenario; arithmetic canopy-footprint proxy from tree count, canopy per tree, effectiveness/survival fraction and corridor area. **NOT** modeled thermal outcomes or real-world shade.
3. Scenario Evidence Passport with official-source link and explicit observed/assumed/not validated states.
4. Construction-worker heat safety guidance: user-selected Dubai local date, time, work setting and English/Bangla/Arabic explanation of the seasonal UAE midday restriction. No live workplace heat assessment, SMS, voice alerts or cooling-site geolocation. Not authoritative medical or legal advice.
5. Manual carbon-and-cost wallet for a commuting scenario, using user-entered fares and clearly labeled 2026 UK factor proxies from existing GreenMiles. No bank connection or transaction categorization.
6. Home climate resilience self-assessment with ranked practical investigation checklist. No photo recognition, engineering certification or prediction of flood probability.
7. Fridge ingredient-by-date prioritization with basic deterministic meal prompts. No camera recognition, spoilage detection or food-safety decision.
8. Climate insurance coverage literacy (questions to ask, not insurance matching or product recommendations).

## Access paths after deployment
- `/` — homepage, updated tiles and COP31 spotlight
- `/app/` — existing application, new COP31 Lab spotlight
- `/app/cop31-lab/` — new lab
- `/app/action-atlas/` — existing Action Atlas

## Important safety and evidence
- Site does not calculate individualized safe work duration, heat illness probability or worker medical risk. It should not be deployed as a production worker alert platform without occupational health validation, WBGT sensor integration, emergency escalation and language review.
- Dubai summer midday ban: generally 15 June to 15 September, 12:30–15:00 outdoors in direct sun, subject to specific exceptions: https://u.ae/en/information-and-services/jobs/health-and-safety-at-workplace
- Dubai heat guidance: https://www.dm.gov.ae/wp-content/uploads/2024/07/DM-HSD-GU38-MHSW2_Technical-Guidelines-for-Management-of-Heat-Stress-at-Work_V3.pdf
- Emissions assumptions: car 0.16591 kgCO2e/vehicle-km, bus 0.10151 kg/passenger-km, rail 0.02121 kg/passenger-km, originally sourced in the platform from the UK government conversion factors (https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026). Dubai-specific mode factors and prices are not validated.
- Satellite land cover, Landsat thermal workflows and neighborhood concepts exist in the prior Action Atlas baseline, but this new Lab does not ingest new Dubai-specific satellite imagery.
- The new Lab does **not** implement Groq yet. Lumi's local assistant remains as in v3.3.
- The project was based on the existing Veritas version, and this document identifies new COP31 additions; do not claim pre-existing work was built during COP31.

## Deploy
1. Create an independent COP31 GitHub repository based on the frozen Veritas final commit. Follow event rules regarding use of pre-existing code.
2. Merge this release onto the COP31 branch or copy the distribution into that repository. Preserve the original Veritas repository/deployment unchanged.
3. Deploy the `dist/` static folder as the Vercel output directory. Ensure nested `/app/cop31-lab/` and `/app/action-atlas/` directory indexes resolve on the hosting platform. Deploy the FastAPI backend separately if backend-dependent features are used.
4. In a browser, test every calculator and form on mobile and desktop, verify the external sources, and check console/network logs.
5. Verify no .env files or secrets are committed before pushing.

## Checks performed
- `node --check dist/app/cop31-lab/lab.js` and `node --check dist/app/app.js` passed.
- An isolated Node DOM-stub smoke test passed eight functional checks covering calculation, walkthrough, heat guidance in two languages, wallet, home, fridge and insurance.
- Automated Chromium execution was blocked by the container administrator, so full end-to-end visual/browser QA could not be completed here.

## Next phase (not included)
- Production Groq tool-calling for Lumi, with server-side key, limits, tool evidence and session handling.
- Verified satellite case-study observations and testable urban intervention model with holdout validation.
- Live worker heat-index data, multi-language professional review, accessible audio/SMS alerts, verified cooling centers and occupational safety partnerships.
- User-consented open-banking integration and merchant-specific lifecycle emissions with vetted factors.
- Computer vision for photo-based home/food workflows and verified insurance-provider comparison.
