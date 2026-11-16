"""Provider ports: the interface handoffs to the other agents' packages.

Stdlib-only (no pydantic) so other packages can implement them without importing the API.
Providers are SYNC callables (routes run in a threadpool) and MUST set their own network
timeouts. Return plain dicts (or objects with model_dump()); the API validates them
against the contract models and answers 502 `provider_contract_violation` on mismatch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


class ProviderUnavailable(Exception):
    """Upstream data source failed/timed out. The API will serve stale cache (if allowed) or 503."""


class InvalidInput(Exception):
    """Domain-level rejection of user input. str(exc) must be safe to show to the user (-> HTTP 422)."""


@runtime_checkable
class WeatherProvider(Protocol):
    def fetch_hourly(self, *, city_id: str, latitude: float, longitude: float, timezone: str, hours: int) -> Sequence[Mapping[str, Any]]:
        """Return HourConditions dicts (contracts/data-models.json), ascending by timestamp, each with Evidence."""


@runtime_checkable
class ClimateEngine(Protocol):
    def rank_windows(self, *, hours: Sequence[Mapping[str, Any]], params: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        """Return ActivityWindow dicts. `params` keys: activity, window_minutes, max_windows,
        comfort_min_c, comfort_max_c, location (coarsened {latitude, longitude} or None).
        Raise InvalidInput for unknown activity etc."""


@runtime_checkable
class ChoicesEngine(Protocol):
    def compare(self, *, kind: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """kind in {travel, food, energy}. Return a ChoiceComparison dict. Own all domain validation (raise InvalidInput)."""


@runtime_checkable
class PlacesProvider(Protocol):
    def list_places(self, *, city_id: str, category: str | None, limit: int) -> Sequence[Mapping[str, Any]]:
        """Each item needs: id, name, data_status, evidence (list of Evidence). Extra fields pass through."""


@runtime_checkable
class BusinessEvidenceProvider(Protocol):
    def get_profile(self, business_id: str) -> Mapping[str, Any] | None:
        """Needs: id, disclosure_status, evidence (list of Evidence). None => unknown id (404)."""


@dataclass
class Providers:
    weather: WeatherProvider | None = None
    climate: ClimateEngine | None = None
    choices: ChoicesEngine | None = None
    places: PlacesProvider | None = None
    business: BusinessEvidenceProvider | None = None

    def status(self) -> dict[str, str]:
        return {
            name: ("bound" if getattr(self, name) is not None else "not_integrated")
            for name in ("weather", "climate", "choices", "places", "business")
        }
