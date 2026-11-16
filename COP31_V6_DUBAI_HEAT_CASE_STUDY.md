# LUNARIS COP31 v6 — Dubai's Thermal Paradox

## Summary

New integrated evidence-led Action case-study page:

`/app/action-atlas/dubai-heat-case/`

The homepage and Action Atlas include prominent links.

### What is REAL and sourced

- Peer-reviewed *Sustainable Cities and Society* study (2026), DOI [10.1016/j.scs.2026.107762](https://doi.org/10.1016/j.scs.2026.107762): mean daytime UHI **−0.4°C**, most vulnerable-zone nighttime intensity **up to +5°C**, study's reported Random Forest importance for surface albedo **62%**. These are *the authors' published findings*, NOT LUNARIS outputs or measured improvement.
- Original study used 2022–2024 MODIS/Landsat/Sentinel-2 and local climate-zone analyses. Its spatial data were not acquired or independently reanalyzed for this release. Study's underlying dataset available on request from authors.
- NASA POWER official API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/ . NASA POWER is a coarse gridded/reanalysis-based daily atmospheric dataset, not hyperlocal surface-heat mapping.

### What LUNARIS itself computes

- Browser scenario: length × width × assumed shade fraction. **This is a ground-area arithmetic model**, not an air-temperature model.
- Reproducible data pipeline: `research/dubai_heat_case.py` downloads NASA POWER 2024–2025 daily ambient `T2M_MAX`, `T2M`, and `RH2M` for Dubai reference coordinates 25.2769°N, 55.2962°E; it saves original daily records, checks missingness, summarizes summer means, and evaluates *simple* previous-day and previous-year baseline errors against a held-out 2025 summer period. Neither is an AI model. These atmospheric results cannot reproduce LCZ thermal differences.

### Validated release snapshot

The final COP31 release ran the pipeline against the official NASA POWER API and bundles `nasa_power_metrics.json`: 731 complete daily records, zero missing days, and 92 matched evaluation days. The 2025 previous-day baseline MAE is 0.8554°C and the prior-year-day baseline MAE is 1.3702°C. These are descriptive errors for coarse daily atmospheric estimates—not AI performance, neighborhood heat validation or intervention impact.

From project root:

```sh
python research/dubai_heat_case.py --output dist/app/action-atlas/dubai-heat-case/nasa_power_metrics.json
python -m unittest discover -s research -p 'test_*.py'
```

The case-study webpage displays the grid statistics and 2025 simple-baseline errors only when the validated snapshot is present. If it is removed or invalid, the page returns to its honest unavailable state.

### Research question / field-validation path

**Why might a Dubai district appear cool during the day yet retain heat at night, and which interventions should be investigated before cities commit scarce resources?**

1. Obtain and compare daytime/nighttime satellite LST at LCZ level, with a matching rural/bare-desert reference.
2. Assess albedo, built geometry, tree canopy, pedestrian shade and water demand.
3. Collect field UTC-matched air temperature / humidity / sun-shade readings, check land permissions and neighborhood representativeness.
4. Design cooling measures, evaluate with calibrated models and repeat field measurement; never treat a rendered illustration or simple shade-footprint as validated cooling.

The **Dubai Marina corridor is an illustration**, not a claimed study-verified heat hotspot, approved tree-planting site, or measured pedestrian exposure zone.

## Deploy (Codex)

Merge this ZIP into the separate COP31 repository only, preserving later Vercel and API changes. Confirm that `/app/action-atlas/dubai-heat-case/` loads directly from Vercel, the homepage and Atlas links work, the sliders calculate correct shade footprint, and the no-data state is clear. Run the pipeline where outbound NASA API network access is available, inspect its actual output, commit its snapshot, and verify metrics against a manual spot-check of the API response. Do not alter the frozen Veritas submission.
