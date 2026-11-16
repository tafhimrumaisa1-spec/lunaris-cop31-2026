"""Transparent what-if calculations; never predictive ML or site-specific impact estimates."""
from math import isfinite

class ScenarioError(ValueError):
    pass

# Units and calculation assumptions are editable scenario parameters.
DEFAULTS = {
    "greening": {"unit_benefit": 12.0, "unit_benefit_label": "m² potential mature canopy per surviving tree", "unit_cost": 1400., "survival": .70, "impact_metric": "potential canopy area at maturity", "impact_unit": "m²", "note":"Not a temperature or CO₂ reduction forecast. Canopy area assumes available space, growth and survival; watering and maintenance excluded."},
    "biodiversity": {"unit_benefit": 1.0, "unit_benefit_label": "m² candidate habitat per m² converted", "unit_cost": 50., "survival": .70, "impact_metric": "hypothetical established habitat", "impact_unit": "m²", "note":"Not a biodiversity index. Requires native-species plan, ecological survey and stewardship."},
    "mobility": {"unit_benefit": 1.8, "unit_benefit_label": "assumed shade width (m) per metre", "unit_cost": 2400., "survival": 1., "impact_metric": "potential shade footprint", "impact_unit": "m²", "note":"Geometric shaded-area illustration, not measured cooling or modeled human heat exposure."},
    "solar": {"unit_benefit": 1550., "unit_benefit_label": "illustrative annual kWh per installed kWp", "unit_cost": 4000., "survival": 1., "impact_metric": "illustrative annual solar generation", "impact_unit": "kWh/year", "note":"No roof suitability or emissions savings assumed; yield is adjustable and not measured for a specific roof."},
    "waste": {"unit_benefit": 3.0, "unit_benefit_label": "assumed diverted kg per participant per month", "unit_cost": 200., "survival": .50, "impact_metric": "hypothetical waste diversion", "impact_unit": "kg/month", "note":"Participation is not verified; avoids claiming landfill diversion or emissions reductions."},
    "water": {"unit_benefit": 12.0, "unit_benefit_label": "assumed liters saved daily per point", "unit_cost": 650., "survival": .80, "impact_metric": "hypothetical water saving", "impact_unit": "liters/day", "note":"Illustrative only; requires metered pre/post comparison and confirmation plants remain healthy."},
}

def estimate(category: str, quantity: float, unit_benefit: float | None = None,
             unit_cost: float | None = None, adoption: float | None = None) -> dict:
    if category not in DEFAULTS:
        raise ScenarioError("Unsupported category")
    x = DEFAULTS[category]
    vals = (quantity, unit_benefit, unit_cost, adoption)
    if any(v is not None and (not isfinite(v) or v < 0) for v in vals):
        raise ScenarioError("All scenario inputs must be finite and non-negative")
    if quantity > 100000 or (unit_benefit is not None and unit_benefit > 1e8) or (unit_cost is not None and unit_cost > 1e8):
        raise ScenarioError("Scenario input exceeds demonstration bounds")
    rate = x["survival"] if adoption is None else adoption
    if not 0 <= rate <= 1:
        raise ScenarioError("Adoption/survival rate must be between 0 and 1")
    benefit = x["unit_benefit"] if unit_benefit is None else unit_benefit
    cost = x["unit_cost"] if unit_cost is None else unit_cost
    output = round(quantity * benefit * rate, 2)
    return {"category":category,"quantity":quantity,"adoption":rate,"benefit_per_unit":benefit,
            "cost_aed_per_unit":cost,"potential_impact":output,"impact_metric":x["impact_metric"],
            "impact_unit":x["impact_unit"],"illustrative_budget_aed":round(quantity * cost,2),
            "interpretation":"Scenario arithmetic; not predicted, measured, funded, or approved impact",
            "note":x["note"],"model_kind":"deterministic user-assumption scenario", "scenario_status":"illustrative"}
