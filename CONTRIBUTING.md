# Contributing to LUNARIS

Thank you for helping improve LUNARIS.

## Before opening a change

- Keep forecasts, measurements, estimates, simulations, and user-supplied
  values visibly distinct.
- Do not add fabricated environmental claims, medical recommendations,
  venue details, model results, or source attributions.
- Keep credentials and private user data out of issues, commits, fixtures,
  screenshots, and logs.
- Preserve the established LUNARIS design system unless the change is
  specifically proposing a reviewed visual update.
- Add or update tests for behavior changes.

## Local checks

```powershell
python scripts/preflight.py
node --check dist/app/app.js
node --check dist/app/action-atlas/atlas.js
python -m pytest -q services/api/tests packages/choices/tests packages/places/tests -p no:cacheprovider
```

Live-provider tests are opt-in and require network access. Never replace a
failed provider response with invented data merely to make a test pass.

## Contributions and licensing

Unless explicitly marked otherwise, contributions intentionally submitted
to this repository are accepted under the Apache License 2.0. By submitting
a contribution, you confirm that you have the right to provide it on those
terms. Do not submit third-party imagery, fonts, datasets, or other assets
without documenting their license and source.

The LUNARIS brand and excluded visual assets are governed by [BRAND.md](BRAND.md),
not by the code license.
