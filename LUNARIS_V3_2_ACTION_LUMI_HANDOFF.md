# LUNARIS Action + Lumi v3.2 — Codex handoff

## Deployment
Deploy this entire directory, not merely the `dist/index.html` landing page. Vercel project output directory should be `dist` unless the repo is restructured. Verify `https://<your-domain>/app/` and `https://<your-domain>/app/action-atlas/` after deploy. If using a framework rewrite, ensure `/app/action-atlas/` resolves to `dist/app/action-atlas/index.html`, not to the homepage. Configure backend and PostgreSQL separately as needed; this patch does not solve backend hosting.

## Changes
- `/app/` primary bottom navigation has a highlighted `Action` tab linked directly to `/app/action-atlas/`.
- The public homepage now spotlights the technical Action Atlas and links directly to it.
- Original Action overview remains accessible through `#action` and now has an Atlas shortcut.
- Lumi now has an interactive local knowledge guide with grounded answers on actual session weather, HeatShield, FoodPrint, GreenMiles, WattFlow, Explore and the Action Atlas. It does not use an LLM or pretend to access live environmental science beyond the app data.
- This is not a live deployment; it needs a GitHub push and Vercel redeploy.

## Smoke test
1. Load `/`, click the **Explore the City Opportunity Atlas** button.
2. Load `/app/`, click the new bottom **Action** tab; confirm it opens the full 12-area atlas map.
3. On `/app/`, use Lumi quick questions and free text; check actual forecast response when provider is online and a truthful unavailable reply when offline.
4. Test narrow mobile width, browser back, and deep links `/app/action-atlas/`.
5. Check that Leaflet CSS and JS CDN are reachable, and that backend-backed interest/evidence calls use a configured API origin. If any external service is unavailable, display fallback messages rather than invented results.

## Optional true conversational Lumi, later
Implement a server-side `/v1/lumi/chat` endpoint backed by a hosted LLM. Use retrieval from source-attributed LUNARIS knowledge and strict tool allowlists to read current weather, atlas evidence, and sourced providers; never expose API keys in browser code. Require rate limiting, privacy controls, streaming/error fallback, source links and prompt-injection tests. Without a model API, local intent routing can only cover supported topics, not unrestricted questions.
