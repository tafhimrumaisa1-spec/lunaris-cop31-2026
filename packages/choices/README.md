# lunaris-choices (Agent 03)

GreenMiles, FoodPrint, WattFlow, Planet Choice and ClimEstate availability gate. Stdlib-only Python >= 3.11, no UI, no network calls, no env vars.

```python
from lunaris_choices import compare_travel, compare_food, calculate_energy, get_business_evidence, assess_area
compare_travel({"distance_km": 12, "modes": [{"mode": "car", "occupancy": 2}, {"mode": "bus"}, {"mode": "walk"}], "country_code": "AE"}).to_dict()
```
Every call returns a `ChoiceComparison` (`.to_dict()` is JSON-safe) with `evidence[]`, `assumptions[]`, `warnings[]`; validation problems raise `ValidationFailure(code, message, field)` (-> HTTP 422); unknown ids raise `NotFoundError` (-> 404).

Run tests: `PYTHONPATH=src python3 -m unittest discover -s tests -v` (pytest also works: `pytest`, `pythonpath` is configured).

Data: `src/lunaris_choices/data/factors.json` (**unverified transcription - see HANDOFF**), `source_manifest.json`.
