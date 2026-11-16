# lunaris-places (Agent 03)

Explore place records + filtering. Depends on `lunaris-choices` (validators, evidence types, city gate). No real venues are shipped: `data/curated_places.json` holds three clearly fictional `DEMO` entries. Real entries must carry source_name, source_url (https), license_note, retrieved_at, verified_by or the loader raises.

```python
from lunaris_places import PlaceService
PlaceService().list_places({"city_id": "dubai", "activities": ["walking"], "comfort_max_c": 29, "weather": {...}})
```
Run tests: `PYTHONPATH=src:../choices/src python3 -m unittest discover -s tests -v`
