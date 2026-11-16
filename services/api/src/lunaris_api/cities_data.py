"""City registry seed. Dubai is the only `supported` city at v0 (PRODUCT_BRIEF.md).

Coordinates are approximate city centres, used only for plausibility checks and as the
forecast anchor; they are never a claim of street-level applicability. All non-Dubai
rows are `unsupported`: no weather, model, venue or licensing audit exists for them.
"""
from __future__ import annotations

CITIES: list[dict] = [
    {"id": "dubai", "name": "Dubai", "country_code": "AE", "timezone": "Asia/Dubai",
     "support_status": "supported", "center_lat": 25.2048, "center_lon": 55.2708},
    {"id": "abu-dhabi", "name": "Abu Dhabi", "country_code": "AE", "timezone": "Asia/Dubai",
     "support_status": "unsupported", "center_lat": 24.4539, "center_lon": 54.3773},
    {"id": "london", "name": "London", "country_code": "GB", "timezone": "Europe/London",
     "support_status": "unsupported", "center_lat": 51.5074, "center_lon": -0.1278},
    {"id": "new-york", "name": "New York", "country_code": "US", "timezone": "America/New_York",
     "support_status": "unsupported", "center_lat": 40.7128, "center_lon": -74.0060},
    {"id": "singapore", "name": "Singapore", "country_code": "SG", "timezone": "Asia/Singapore",
     "support_status": "unsupported", "center_lat": 1.3521, "center_lon": 103.8198},
]
