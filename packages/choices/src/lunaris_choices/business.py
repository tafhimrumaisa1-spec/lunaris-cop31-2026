"""Planet Choice: business environmental-claim evidence profiles. No certification, no ranking, no paid placement.

MVP supports only `self_reported` and `documentation_reviewed`. `independently_verified` is a defined status in the
vocabulary but is REJECTED on input until an independent-verification workflow exists (DATA_AND_EVIDENCE.md item 11).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from . import validation as v
from .evidence import Clock, Evidence, NotFoundError, ResultWarning, ValidationFailure, iso_utc, utc_now

CLAIM_STATUSES = ("self_reported", "documentation_reviewed", "independently_verified")
MVP_ALLOWED_STATUSES = ("self_reported", "documentation_reviewed")
CLAIM_TYPES = ("reusable_cups", "refill", "waste_segregation", "public_disclosure", "other")
_FORBIDDEN = re.compile(r"(?<!\w)(certified|certification|accredited|guaranteed|best in|#1|top[- ]ranked)(?!\w)", re.I)
_CLAIM_KEYS = {"claim_type", "text", "status", "disclosure_url", "evidence_url", "reviewer", "reviewed_at", "verifier"}


@dataclass(frozen=True)
class BusinessClaim:
    claim_type: str
    text: str
    status: str
    disclosure_url: Optional[str] = None
    evidence_url: Optional[str] = None
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> "BusinessClaim":
        v.reject_unknown_keys(d, _CLAIM_KEYS, "claim")
        status = v.one_of(d.get("status"), "status", CLAIM_STATUSES)
        if status not in MVP_ALLOWED_STATUSES or d.get("verifier") is not None:
            raise ValidationFailure("VERIFIED_STATUS_NOT_SUPPORTED",
                                    "independently_verified is not supported in this release; it cannot be set or implied.", "status")
        text = v.text(d.get("text"), "text", max_len=300)
        if _FORBIDDEN.search(text):
            raise ValidationFailure("FORBIDDEN_CLAIM_WORDING",
                                    "Claim text must not use certification/ranking language (certified, accredited, guaranteed, #1...).", "text")
        ctype = v.one_of(d.get("claim_type"), "claim_type", CLAIM_TYPES)
        disclosure = v.https_url(d.get("disclosure_url"), "disclosure_url", required=False)
        evidence_url = v.https_url(d.get("evidence_url"), "evidence_url", required=False)
        reviewer = v.text(d.get("reviewer"), "reviewer", max_len=80, required=False)
        reviewed_at = v.aware_datetime(d.get("reviewed_at"), "reviewed_at", required=False)
        if status == "documentation_reviewed":
            missing = [n for n, val in (("evidence_url", evidence_url), ("reviewer", reviewer), ("reviewed_at", reviewed_at)) if not val]
            if missing:
                raise ValidationFailure("REVIEW_RECORD_INCOMPLETE", f"documentation_reviewed requires {missing}", missing[0])
        else:
            if reviewer or reviewed_at or evidence_url:
                raise ValidationFailure("REVIEW_FIELDS_ON_SELF_REPORT", "self_reported claims must not carry reviewer/review fields", "status")
        return BusinessClaim(ctype, text, status, disclosure, evidence_url, reviewer, iso_utc(reviewed_at) if reviewed_at else None)


@dataclass(frozen=True)
class BusinessProfile:
    business_id: str
    display_name: str
    is_demo: bool
    claims: list = field(default_factory=list)


class BusinessEvidenceRepository:
    def __init__(self, profiles=()):
        self._p = {p.business_id: p for p in profiles}

    def add(self, profile: BusinessProfile) -> None:
        if not profile.is_demo:
            raise ValidationFailure("REAL_BUSINESS_NEEDS_PROVENANCE", "Non-demo business profiles are not supported in this release.", "is_demo")
        self._p[profile.business_id] = profile

    def get(self, business_id: str) -> BusinessProfile:
        if not isinstance(business_id, str) or business_id not in self._p:
            raise NotFoundError(f"business '{business_id}' not found")
        return self._p[business_id]


def seeded_repository() -> BusinessEvidenceRepository:
    demo = BusinessProfile("demo-business-001", "DEMO Business (fictional - not a real venue)", True, [
        BusinessClaim("reusable_cups", "Offers discounts for reusable cups (demo data).", "self_reported"),
        BusinessClaim("waste_segregation", "Separates recyclables (demo data).", "documentation_reviewed",
                      evidence_url="https://example.invalid/demo-evidence", reviewer="DEMO reviewer", reviewed_at="2026-01-01T00:00:00Z"),
    ])
    return BusinessEvidenceRepository([demo])


def get_business_evidence(business_id: str, repo: Optional[BusinessEvidenceRepository] = None, *, clock: Clock = utc_now) -> dict:
    p = (repo or seeded_repository()).get(business_id)
    counts = {s: sum(1 for c in p.claims if c.status == s) for s in CLAIM_STATUSES}
    warnings = [
        ResultWarning("NOT_CERTIFICATION", "Evidence profile only. This is not a certification, rating or ranking.", "limitation"),
        ResultWarning("REUSE_DEPENDS", "Whether reusable items beat single-use depends on how often they are reused; no blanket claim is made.", "info"),
    ]
    if p.is_demo:
        warnings.insert(0, ResultWarning("DEMO_DATA", "Fictional demonstration profile; not a real business.", "caution"))
    ev = Evidence("LUNARIS Planet Choice evidence profile", None, iso_utc(clock()), None,
                  "demo" if p.is_demo else "self_reported",
                  "Each claim keeps its own status; statuses are never aggregated into a badge.",
                  ["Independent verification not supported in this release.", "Claims are not audited by LUNARIS beyond the stated review record."])
    return {"business_id": p.business_id, "display_name": p.display_name, "is_demo": p.is_demo,
            "claims": [c.__dict__ for c in p.claims], "status_counts": counts,
            "allowed_statuses_in_this_release": list(MVP_ALLOWED_STATUSES),
            "evidence": [ev], "warnings": warnings}
