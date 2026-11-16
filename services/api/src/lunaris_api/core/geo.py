"""Geolocation privacy helpers. Coordinates are coarsened on entry and never stored."""
from __future__ import annotations

import math

# 2 decimal places is ~1.1 km of latitude: enough for a city-level plausibility
# check, not enough to identify a home/building.
COARSEN_DECIMALS = 2
# Plausibility radius around a city's approximate centre. Not a claim about the city boundary.
DEFAULT_CITY_RADIUS_KM = 80.0


def coarsen(lat: float, lon: float, decimals: int = COARSEN_DECIMALS) -> tuple[float, float]:
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise ValueError("coordinates must be finite")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("coordinates out of range")
    return round(lat, decimals), round(lon, decimals)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def within_radius(lat: float, lon: float, center_lat: float, center_lon: float, radius_km: float = DEFAULT_CITY_RADIUS_KM) -> bool:
    return haversine_km(lat, lon, center_lat, center_lon) <= radius_km
