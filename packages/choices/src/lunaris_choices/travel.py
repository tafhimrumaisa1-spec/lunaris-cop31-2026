"""GreenMiles: mode comparison on a USER-ENTERED distance. No routing, no invented times."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from . import validation as v
from .evidence import ChoiceComparison, Clock, Evidence, ResultWarning, ValidationFailure, iso_utc, utc_now
from .factors import factors_verified, load_factors
from .routing import DisabledRoutingProvider

MODES = ("car", "motorbike", "bus", "metro_rail", "electric_car", "walk", "bicycle")
MAX_DISTANCE_KM = 20000.0
_MODE_KEYS = {"mode", "occupancy", "avg_speed_kmh", "ev_kwh_per_km", "grid_kg_per_kwh"}
_REQ_KEYS = {"distance_km", "modes", "country_code", "round_trip", "baseline_mode"}


@dataclass(frozen=True)
class ModeInput:
    mode: str
    occupancy: Optional[float] = None
    avg_speed_kmh: Optional[float] = None
    ev_kwh_per_km: Optional[float] = None
    grid_kg_per_kwh: Optional[float] = None

    @staticmethod
    def from_dict(d: dict) -> "ModeInput":
        v.reject_unknown_keys(d, _MODE_KEYS, "mode entry")
        mode = v.one_of(d.get("mode"), "mode", MODES)
        spec = load_factors()["travel"]["modes"][mode]
        occ = v.number(d.get("occupancy"), "occupancy", ge=1, le=spec.get("max_occupancy", 9), required=False)
        return ModeInput(
            mode=mode, occupancy=occ,
            avg_speed_kmh=v.number(d.get("avg_speed_kmh"), "avg_speed_kmh", gt=0, le=1000, required=False),
            ev_kwh_per_km=v.number(d.get("ev_kwh_per_km"), "ev_kwh_per_km", gt=0, le=3, required=False),
            grid_kg_per_kwh=v.number(d.get("grid_kg_per_kwh"), "grid_kg_per_kwh", ge=0, le=2, required=False),
        )


@dataclass(frozen=True)
class TravelRequest:
    distance_km: float
    modes: list
    country_code: str = "AE"
    round_trip: bool = False
    baseline_mode: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> "TravelRequest":
        if isinstance(d, dict) and ({"origin", "destination", "start", "end"} & set(d)):
            raise ValidationFailure("ROUTING_DISABLED",
                                    "Origin/destination routing is disabled (no licensed provider). Provide distance_km and modes.")
        v.reject_unknown_keys(d, _REQ_KEYS, "travel request")
        dist = v.number(d.get("distance_km"), "distance_km", gt=0, le=MAX_DISTANCE_KM)
        modes_raw = d.get("modes")
        if not isinstance(modes_raw, list) or not (1 <= len(modes_raw) <= len(MODES)):
            raise ValidationFailure("BAD_MODES", f"modes must be a list of 1..{len(MODES)} entries", "modes")
        modes = [ModeInput.from_dict(m) for m in modes_raw]
        if len({m.mode for m in modes}) != len(modes):
            raise ValidationFailure("DUPLICATE_MODE", "each mode may appear once", "modes")
        rt = d.get("round_trip", False)
        if not isinstance(rt, bool):
            raise ValidationFailure("NOT_A_BOOLEAN", "round_trip must be boolean", "round_trip")
        base = d.get("baseline_mode")
        if base is not None:
            base = v.one_of(base, "baseline_mode", [m.mode for m in modes])
        return TravelRequest(dist, modes, v.country_code(d.get("country_code", "AE")), rt, base)


def _r(x: float) -> float:
    return round(x, 5)


def compare_travel(request, *, clock: Clock = utc_now) -> ChoiceComparison:
    req = request if isinstance(request, TravelRequest) else TravelRequest.from_dict(request)
    F = load_factors()["travel"]
    now = clock()
    total_km = req.distance_km * (2 if req.round_trip else 1)
    warnings: list = [ResultWarning("NO_ROUTING", DisabledRoutingProvider.reason + " Distance is user-entered; no route, time or traffic is estimated.", "limitation")]
    assumptions = [
        f"Distance used: {total_km:g} km ({'round trip' if req.round_trip else 'one way'}) as entered by the user.",
        f"Factors: {F['source_name']} {F['year']} ({F['jurisdiction']} jurisdiction). Boundary: {F['boundary']}",
    ]
    if not factors_verified():
        warnings.append(ResultWarning("FACTORS_UNVERIFIED",
                                      "Emission factors are an unverified transcription of the cited source; check source_url before relying on figures.", "caution"))
    if req.country_code != F["jurisdiction"]:
        warnings.append(ResultWarning("JURISDICTION_PROXY",
                                      f"Factors are {F['jurisdiction']} values used as a proxy for {req.country_code}; no {req.country_code}-specific or transit-operator (e.g. RTA) factor is adopted.", "caution"))
        assumptions.append(f"{F['jurisdiction']} factors applied to country {req.country_code} as a proxy.")

    alts = []
    speeds_missing = False
    for m in req.modes:
        spec = F["modes"][m.mode]
        alt = {"mode": m.mode, "status": "calculated", "unit": "kg CO2e", "notes": []}
        if m.mode == "electric_car":
            if m.ev_kwh_per_km is None or m.grid_kg_per_kwh is None:
                alt.update(status="excluded", reason="electric_car requires user-supplied ev_kwh_per_km and grid_kg_per_kwh; no grid factor is assumed.")
                warnings.append(ResultWarning("EV_INPUT_MISSING", alt["reason"], "caution"))
                alts.append(alt)
                continue
            occ = m.occupancy or 1.0
            c = total_km * m.ev_kwh_per_km * m.grid_kg_per_kwh / occ
            low = high = c
            alt["notes"].append("Single-point value from user inputs; no range. Excludes manufacturing and battery lifecycle.")
            alt["occupancy"] = occ
        elif spec["basis"] == "vehicle":
            occ = m.occupancy or 1.0
            if m.occupancy is None:
                assumptions.append(f"{m.mode}: occupancy not given; assumed {occ:g} (driver only).")
            low, c, high = (total_km * spec[k] / occ for k in ("low", "central", "high"))
            alt["occupancy"] = occ
            alt["range_basis"] = spec["range_basis"]
        elif spec["basis"] == "passenger":
            if m.occupancy is not None:
                warnings.append(ResultWarning("OCCUPANCY_IGNORED", f"{m.mode}: factor is already per passenger-km at average loading; occupancy input ignored.", "info"))
            low, c, high = (total_km * spec[k] for k in ("low", "central", "high"))
            alt["range_basis"] = spec["range_basis"]
        else:  # walk / bicycle
            low = c = high = 0.0
            alt["notes"].append(spec["lifecycle_note"])
        alt["emissions_kg_co2e"] = {"low": _r(low), "central": _r(c), "high": _r(high)}
        if m.avg_speed_kmh:
            alt["time_minutes"] = _r(total_km / m.avg_speed_kmh * 60)
            alt["time_basis"] = "user-entered average speed; excludes waiting, traffic, access/egress"
        else:
            alt["time_minutes"] = None
            speeds_missing = True
        alts.append(alt)
    if speeds_missing:
        warnings.append(ResultWarning("TIME_NOT_PROVIDED", "Travel time is only shown for modes where an average speed was entered.", "info"))
    calc = [a for a in alts if a["status"] == "calculated"]

    impacts = []
    baseline = None
    if calc:
        baseline = next((a for a in calc if a["mode"] == req.baseline_mode), None) if req.baseline_mode else None
        if req.baseline_mode and baseline is None:
            raise ValidationFailure("BASELINE_EXCLUDED", "baseline_mode could not be calculated (missing inputs)", "baseline_mode")
        baseline = baseline or max(calc, key=lambda a: a["emissions_kg_co2e"]["central"])
        assumptions.append(f"Differences are measured against baseline mode '{baseline['mode']}'" + ("" if req.baseline_mode else " (highest central estimate, default)."))
        b = baseline["emissions_kg_co2e"]
        for a in calc:
            if a is baseline:
                continue
            e = a["emissions_kg_co2e"]
            lo, hi = e["low"] - b["high"], e["high"] - b["low"]
            impacts.append({
                "mode": a["mode"], "baseline_mode": baseline["mode"], "unit": "kg CO2e",
                "difference_central": _r(e["central"] - b["central"]),
                "difference_low": _r(lo), "difference_high": _r(hi),
                "range_includes_zero": lo <= 0 <= hi,
            })
    ev = Evidence(
        source_name=F["source_name"], source_url=F["source_url"], retrieved_at=iso_utc(now), valid_at=None,
        data_status="modeled",
        method=f"distance x per-km factor ({F['year']} edition), divided by occupancy for vehicle-based modes; ranges from published vehicle-size/loading variants.",
        limitations=["User-entered distance; not a routed path.", "Factors are national averages, not specific vehicles or Dubai fleets.",
                     "Walk/bicycle operational emissions only.", F["boundary"]],
    )
    key = json.dumps({"d": req.distance_km, "rt": req.round_trip, "c": req.country_code,
                      "m": [m.__dict__ for m in req.modes]}, sort_keys=True)
    cid = "travel:" + hashlib.sha1(key.encode()).hexdigest()[:12]
    return ChoiceComparison(cid, "travel", alts, impacts, assumptions, [ev], warnings)
