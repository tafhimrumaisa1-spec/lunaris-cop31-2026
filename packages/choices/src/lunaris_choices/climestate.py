"""ClimEstate: data-availability gate. No hazard score is ever produced without validated, licensed, area-level datasets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .cities import city_status
from .evidence import Clock, Evidence, ResultWarning, iso_utc, utc_now


@dataclass(frozen=True)
class ValidatedDataset:
    dataset_id: str
    hazard: str  # "heat" | "flood"
    city_id: str
    spatial_resolution: str
    license_reviewed: bool
    validation_report_url: Optional[str]

    def passes_gate(self) -> bool:
        return bool(self.license_reviewed and self.validation_report_url)


EXPLAINER = [
    "ClimEstate is intended to describe AREA-LEVEL exposure to hazards such as extreme heat and flooding, using published, validated datasets.",
    "Heat exposure at area level is shaped by climate, urban form, shade and cooling access; flood exposure depends on drainage, terrain and extreme-rainfall frequency.",
    "This is not a property safety assessment, insurance opinion or investment advice.",
]
CANDIDATES = [
    {"kind": "published government flood-hazard / drainage maps", "status": "not integrated", "reason": "no dataset selected, licensed or validated"},
    {"kind": "area-level urban heat / land-surface-temperature products", "status": "not integrated", "reason": "no dataset selected, licensed or validated"},
]


def assess_area(city_id: str, area_query: Optional[str] = None, registry=(), *, clock: Clock = utc_now) -> dict:
    status = city_status(city_id)
    usable = [d for d in registry if d.passes_gate() and d.city_id == str(city_id).strip().lower()] if status == "supported" else []
    warnings = [ResultWarning("NOT_ASSESSED", "No hazard has been assessed. Risks are hidden until supported datasets are validated.", "limitation"),
                ResultWarning("NOT_ADVICE", "Not property safety, insurance or investment advice.", "limitation")]
    if status != "supported":
        warnings.insert(0, ResultWarning("UNSUPPORTED_CITY", f"City '{city_id}' has no supported coverage.", "limitation"))
    reason = ("city_unsupported" if status != "supported" else
              "validated_dataset_present_but_no_hazard_adapter_in_this_release" if usable else "no_validated_dataset")
    ev = Evidence("LUNARIS ClimEstate availability gate", None, iso_utc(clock()), None, "demo", "dataset-availability check only; no hazard computation",
                  ["No parcel-level data.", "No hazard scores are produced."])
    return {"city_id": city_id, "area_query": area_query, "support_status": status,
            "assessment_status": "not_assessed", "reason": reason, "hazards": [],
            "explainer": EXPLAINER, "datasets_considered": CANDIDATES,
            "validated_datasets": [d.dataset_id for d in usable], "evidence": [ev], "warnings": warnings}
