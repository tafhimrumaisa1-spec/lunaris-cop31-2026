# Codex integration — LUNARIS Action City Opportunity Atlas

The new module is already implemented in the supplied project. **Do not rebuild it**. Integrate/deploy it with the existing application.

1. Read `docs/ACTION_ATLAS_INTEGRATION.md` and `README_INTEGRATED.md`.
2. The existing consumer Action screen links to `/app/action-atlas/`.
3. The working Atlas UI lives in `dist/app/action-atlas/` and uses the same near-black, lime, ivory editorial design language as LUNARIS.
4. FastAPI routes are registered in `services/api/src/lunaris_api/app.py` and implemented in `routers/action_atlas.py`.
5. Run the included API and frontend. Verify area selection, map filters, scenario adjustments, downloaded brief, consent-based join-interest and fallback when API is offline.
6. Obtain real Earth Engine data by running `services/api/src/lunaris_api/action_atlas/export_gee.js` on an authorized account. Treat results as unvalidated until checked; do not display fake heat or greenery statistics in the UI.
7. Preserve the mapping between area-scale case proposals and Dubai's official strategy. Do not infer exact planting spots from neighborhood centroids.
8. A production version needs official permission processes, field-verified opportunities, moderated campaigns, authenticated identities and a verified partner workflow. Current consented interest is only for demo concepts.
9. Run `PYTHONPATH=src:. pytest -q tests` from `services/api`, plus `node --check dist/app/action-atlas/atlas.js`.
10. Keep the illustrated city marketing homepage and the working HeatShield/Climate AI integration unchanged.

## Final demo path
- Home → Try Platform → Action → Open Dubai Opportunity Atlas.
- Change layers, select Dubai Marina (concept area), inspect action constraints, change hypothetical tree count and survival assumption, view estimated mature canopy footprint, download brief, and record **concept-only** interest.
- Show the explicit status disclosure: no satellite detections, permits, planting locations, verified volunteers or environmental improvements are currently claimed.
- Discuss optional Earth Engine indicator export and real-world partner approval as the next evidence gates.
