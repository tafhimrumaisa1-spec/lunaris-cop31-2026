"""FoodPrint: two-category comparison using published category-average factors. Never brand/restaurant specific."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from . import validation as v
from .evidence import ChoiceComparison, Clock, Evidence, ResultWarning, ValidationFailure, iso_utc, utc_now
from .factors import factors_verified, load_factors

MAX_GRAMS = 100_000.0
_ITEM_KEYS = {"category", "quantity_g", "label"}
_REQ_KEYS = {"item_a", "item_b"}


def list_categories() -> list:
    F = load_factors()["food"]
    return [{"id": k, "label": c["label"], "unit": F["unit"]} for k, c in F["categories"].items()]


@dataclass(frozen=True)
class FoodItem:
    category: str
    quantity_g: float
    label: Optional[str] = None

    @staticmethod
    def from_dict(d: dict, name: str) -> "FoodItem":
        v.reject_unknown_keys(d, _ITEM_KEYS, name)
        cats = load_factors()["food"]["categories"]
        cat = d.get("category")
        if not isinstance(cat, str) or cat not in cats:
            raise ValidationFailure("UNSUPPORTED_CATEGORY",
                                    f"{name}.category must be a documented food category {sorted(cats)}; brand/restaurant/product names are not supported.", f"{name}.category")
        return FoodItem(cat, v.number(d.get("quantity_g"), f"{name}.quantity_g", gt=0, le=MAX_GRAMS),
                        v.text(d.get("label"), f"{name}.label", max_len=80, required=False))


def compare_food(request: dict, *, clock: Clock = utc_now) -> ChoiceComparison:
    v.reject_unknown_keys(request, _REQ_KEYS, "food request")
    a, b = FoodItem.from_dict(request.get("item_a"), "item_a"), FoodItem.from_dict(request.get("item_b"), "item_b")
    F = load_factors()["food"]
    rows = []
    for it in (a, b):
        f = F["categories"][it.category]["factor"]
        kg = it.quantity_g / 1000
        rows.append({"category": it.category, "category_label": F["categories"][it.category]["label"],
                     "user_label": it.label, "quantity_g": it.quantity_g,
                     "factor": f, "factor_unit": F["unit"],
                     "emissions_kg_co2e": {"central": round(f * kg, 5), "low": None, "high": None},
                     "emissions_unit": "kg CO2e", "year": F["year"], "boundary": F["boundary"]})
    ea, eb = rows[0]["emissions_kg_co2e"]["central"], rows[1]["emissions_kg_co2e"]["central"]
    impact = {"unit": "kg CO2e", "item_a_minus_item_b": round(ea - eb, 5), "range": None,
              "ratio_a_to_b": round(ea / eb, 3) if eb > 0 else None,
              "equal_quantities": a.quantity_g == b.quantity_g}
    warnings = [
        ResultWarning("CATEGORY_AVERAGE", "Figures are global category averages, not any specific product, brand, recipe or restaurant.", "limitation"),
        ResultWarning("RANGE_NOT_ENCODED", F["uncertainty"], "caution"),
    ]
    if not factors_verified():
        warnings.append(ResultWarning("FACTORS_UNVERIFIED", "Factors are an unverified transcription; check source_url before relying on figures.", "caution"))
    if not impact["equal_quantities"]:
        warnings.append(ResultWarning("UNEQUAL_QUANTITIES", "Quantities differ; the difference reflects both category and amount (not nutrition-equivalent).", "info"))
    if any(r["user_label"] for r in rows):
        warnings.append(ResultWarning("LABEL_NOT_USED", "Free-text labels are echoed only; the calculation uses the category average.", "info"))
    ev = Evidence(F["source_name"], F["source_url"], iso_utc(clock()), None, "modeled",
                  "quantity (kg) x published kg CO2e per kg category factor",
                  [F["boundary"], F["uncertainty"], "Comparison is by mass, not nutrition or protein equivalence."])
    key = json.dumps([a.__dict__, b.__dict__], sort_keys=True)
    return ChoiceComparison("food:" + hashlib.sha1(key.encode()).hexdigest()[:12], "food", rows, [impact],
                            [f"Factors: {F['source_name']} ({F['year']}), {F['unit']}.", "No cooking, transport-to-home, or waste adjustments."],
                            [ev], warnings)
