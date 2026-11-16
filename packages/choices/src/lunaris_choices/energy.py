"""WattFlow: appliance what-if. kWh and AED cost from USER inputs only; no tariff or meter is assumed."""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from . import validation as v
from .evidence import ChoiceComparison, Clock, Evidence, ResultWarning, ValidationFailure, iso_utc, utc_now

_SC_KEYS = {"name", "power_w", "hours_per_use", "uses_per_week", "duty_cycle"}
_REQ_KEYS = {"scenarios", "period_days", "tariff_aed_per_kwh", "grid_kg_per_kwh"}
MAX_POWER_W = 100_000.0


def _scenario(d: dict, i: int) -> dict:
    n = f"scenarios[{i}]"
    v.reject_unknown_keys(d, _SC_KEYS, n)
    hours = v.number(d.get("hours_per_use"), f"{n}.hours_per_use", gt=0, le=24)
    uses = v.number(d.get("uses_per_week"), f"{n}.uses_per_week", gt=0, le=168)
    if hours * uses > 168:
        raise ValidationFailure("IMPOSSIBLE_DURATION", f"{n}: hours_per_use x uses_per_week exceeds 168 h in a week", n)
    duty = v.number(d.get("duty_cycle", 1.0), f"{n}.duty_cycle", gt=0, le=1)
    return {"name": v.text(d.get("name"), f"{n}.name", max_len=80),
            "power_w": v.number(d.get("power_w"), f"{n}.power_w", gt=0, le=MAX_POWER_W),
            "hours_per_use": hours, "uses_per_week": uses, "duty_cycle": duty}


def calculate_energy(request: dict, *, clock: Clock = utc_now) -> ChoiceComparison:
    v.reject_unknown_keys(request, _REQ_KEYS, "energy request")
    sc_raw = request.get("scenarios")
    if not isinstance(sc_raw, list) or not (1 <= len(sc_raw) <= 5):
        raise ValidationFailure("BAD_SCENARIOS", "scenarios must be a list of 1..5 entries", "scenarios")
    scs = [_scenario(s, i) for i, s in enumerate(sc_raw)]
    period = v.number(request.get("period_days", 30), "period_days", gt=0, le=366)
    tariff = v.number(request.get("tariff_aed_per_kwh"), "tariff_aed_per_kwh", ge=0, le=100, required=False)
    grid = v.number(request.get("grid_kg_per_kwh"), "grid_kg_per_kwh", ge=0, le=2, required=False)

    warnings = [ResultWarning("NO_METER_DATA", "Scenario arithmetic on user-entered values; not a forecast of actual household usage and no smart-meter data is used.", "limitation")]
    assumptions = [f"Period: {period:g} days.", "kWh = power_w/1000 x duty_cycle x hours_per_use x uses_per_week x (period_days/7)."]
    if tariff is None:
        warnings.append(ResultWarning("UNKNOWN_PRICE", "No tariff entered, so cost is not calculated. DEWA tariffs are not integrated; enter your own AED/kWh.", "caution"))
    else:
        assumptions.append(f"Tariff {tariff:g} AED/kWh is a user-entered custom assumption (flat rate); DEWA slabs, surcharges and fuel adjustments are not modelled.")
        if tariff == 0:
            warnings.append(ResultWarning("ZERO_TARIFF", "Tariff of 0 AED/kWh entered; costs will be 0.", "info"))
    if grid is None:
        warnings.append(ResultWarning("NO_EMISSIONS_FACTOR", "No grid emissions factor entered, so emissions are not calculated.", "info"))
    else:
        assumptions.append(f"Grid factor {grid:g} kg CO2e/kWh is user-entered.")
    rows = []
    for s in scs:
        kwh = s["power_w"] / 1000 * s["duty_cycle"] * s["hours_per_use"] * s["uses_per_week"] * (period / 7)
        rows.append({**s, "period_days": period, "energy_kwh": round(kwh, 4), "energy_unit": "kWh",
                     "cost_aed": round(kwh * tariff, 2) if tariff is not None else None,
                     "cost_status": "custom_assumption" if tariff is not None else "unknown",
                     "emissions_kg_co2e": round(kwh * grid, 4) if grid is not None else None})
    base = rows[0]
    impacts = []
    for r in rows[1:]:
        impacts.append({"scenario": r["name"], "baseline": base["name"],
                        "energy_kwh_difference": round(r["energy_kwh"] - base["energy_kwh"], 4), "energy_unit": "kWh",
                        "cost_aed_difference": round(r["cost_aed"] - base["cost_aed"], 2) if tariff is not None else None,
                        "emissions_kg_co2e_difference": round(r["emissions_kg_co2e"] - base["emissions_kg_co2e"], 4) if grid is not None else None})
    ev = Evidence("User-entered scenario (LUNARIS WattFlow arithmetic)", None, iso_utc(clock()), None, "modeled",
                  "energy = power x duty cycle x hours; cost = energy x user tariff",
                  ["Not measured consumption.", "Tariff is a custom assumption, not the official DEWA tariff.",
                   "Net bill savings cannot be claimed without actual usage data."])
    key = json.dumps([request.get("scenarios"), period, tariff, grid], sort_keys=True, default=str)
    return ChoiceComparison("energy:" + hashlib.sha1(key.encode()).hexdigest()[:12], "energy", rows, impacts, assumptions, [ev], warnings)
