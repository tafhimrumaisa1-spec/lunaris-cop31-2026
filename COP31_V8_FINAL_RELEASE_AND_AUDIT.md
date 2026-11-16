# LUNARIS COP31 v8 — Final Guided Walkthrough Release

## What changed in v8
- Added `/tour/`: accessible 10-step interactive guided walkthrough mapping the mission, three intelligence layers, all major modules, Action Atlas, Dubai heat study, Lumi, evidence status and future work.
- Added a small floating **Explore LUNARIS** launcher to **all nine existing HTML entry points**, linking to `/tour/`. On small screens it sits above the bottom navigation.
- Linked the homepage three-intelligence map directly to the guided tour.
- Included independent Next/Previous and direct step selection, plus links to the actual application pages.
- No new API calls, data collection, keys, or claims about measured climate outcomes were introduced.

## Combined version audit (v3.2–v8)
- Action Atlas navigation and Dubai neighborhood concepts: INCLUDED in ZIP.
- Main Lumi bottom entry + local bounded Lumi guide: INCLUDED. **Groq-powered Lumi is NOT bundled as a working production integration**; retrieve and merge the deployed implementation from the current GitHub repo.
- COP31 Action & Resilience Lab: INCLUDED.
- Construction-worker heat guidance: INCLUDED as a multilingual policy/time demo; NO live SMS, WBGT model or verified cooling locations.
- Carbon & Cost Wallet: INCLUDED as manual comparison with factor assumptions; no bank API.
- Fridge Brain in FoodPrint, Home Resilience in WattFlow, climate insurance guide: INCLUDED as linked experiences and standalone routes; no camera AI or live insurance quotes.
- COP31 ten-card homepage, dedicated Wallet navigation and Insurance entry: INCLUDED.
- Dubai heat case-study page and NASA POWER reproducible script/tests: INCLUDED. **Completed NASA POWER dataset/results are NOT guaranteed to be in this archive**. Preserve actual verified JSON outputs from current GitHub repo.
- New cover poster and updated H1: INCLUDED as optional image and homepage HTML respectively.
- Three-intelligence branch architecture: INCLUDED.
- Guided `/tour/` and floating Explore LUNARIS launcher: INCLUDED in v8.

## Deployment safety
1. Preserve frozen Veritas project unchanged.
2. Merge this archive into the COP31 repo, comparing against any already deployed live Groq and NASA integrations before overwriting ANY file.
3. Confirm Vercel production static output root is `dist/` and nested routes such as `/tour/` and `/app/action-atlas/dubai-heat-case/` resolve. Adapt to the actual deploy setup.
4. Verify API secrets remain in server-side environment variables and are NOT present in `dist/` or committed files.
5. Complete automated tests and real-browser mobile/desktop checks.
6. Explicitly report whether the public Groq assistant and NASA metrics are connected in the deployed final build.

## Important provenance
This package is the latest local snapshot of the iterative prototype. It does not automatically contain changes made independently in Codex or the user's live repository. Use Git diff/merge, not a blind copy. Preserve the date/commit history of pre-existing Veritas development and accurately identify COP31-period contributions in submissions.
