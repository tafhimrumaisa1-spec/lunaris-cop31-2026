"""Place records with mandatory provenance. Demo entries must be unmistakably labelled; real entries need licensed/curated source."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from lunaris_choices import validation as v
from lunaris_choices.evidence import Evidence, ValidationFailure, iso_utc

CATEGORIES = ("cafe", "walk", "indoor", "culture", "event")
SETTINGS = ("indoor", "outdoor", "mixed")
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
HOURS_MAX_AGE = timedelta(days=30)
_KEYS = {"id", "name", "city_id", "categories", "setting", "is_demo", "description", "map_link", "hours", "hours_verified_at",
         "source_name", "source_url", "license_note", "retrieved_at", "verified_by"}


def _parse_hours(h) -> Optional[dict]:
    if h is None:
        return None
    if not isinstance(h, dict) or set(h) - set(DAYS):
        raise ValidationFailure("BAD_HOURS", f"hours must be an object keyed by {DAYS}", "hours")
    out = {}
    for day, ranges in h.items():
        if not isinstance(ranges, list):
            raise ValidationFailure("BAD_HOURS", "each day must be a list of [open, close] pairs", "hours")
        parsed = []
        for r in ranges:
            if not (isinstance(r, list) and len(r) == 2):
                raise ValidationFailure("BAD_HOURS", "range must be [HH:MM, HH:MM]", "hours")
            try:
                parsed.append(tuple(datetime.strptime(x, "%H:%M").time() for x in r))
            except (ValueError, TypeError):
                raise ValidationFailure("BAD_HOURS", "times must be HH:MM", "hours")
        out[day] = parsed
    return out


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    city_id: str
    categories: tuple
    setting: str
    is_demo: bool
    description: str
    map_link: Optional[str]
    hours: Optional[dict]
    hours_verified_at: Optional[datetime]
    source_name: Optional[str]
    source_url: Optional[str]
    license_note: Optional[str]
    retrieved_at: Optional[datetime]
    verified_by: Optional[str]

    @staticmethod
    def from_dict(d: dict) -> "Place":
        v.reject_unknown_keys(d, _KEYS, "place")
        is_demo = d.get("is_demo")
        if not isinstance(is_demo, bool):
            raise ValidationFailure("MISSING_FIELD", "is_demo must be explicitly true or false", "is_demo")
        name = v.text(d.get("name"), "name", max_len=120)
        cats = d.get("categories")
        if not isinstance(cats, list) or not cats:
            raise ValidationFailure("BAD_CATEGORIES", "categories must be a non-empty list", "categories")
        cats = tuple(v.one_of(c, "categories[]", CATEGORIES) for c in cats)
        if is_demo:
            if not name.upper().startswith("DEMO"):
                raise ValidationFailure("DEMO_NAME_REQUIRED", "demo place names must start with 'DEMO'", "name")
        else:
            missing = [k for k in ("source_name", "source_url", "license_note", "retrieved_at", "verified_by") if not d.get(k)]
            if missing:
                raise ValidationFailure("MISSING_PROVENANCE", f"non-demo place requires {missing}", missing[0])
        hv = v.aware_datetime(d.get("hours_verified_at"), "hours_verified_at", required=False)
        hours = _parse_hours(d.get("hours"))
        if hours and not hv:
            raise ValidationFailure("HOURS_UNVERIFIED", "hours require hours_verified_at", "hours_verified_at")
        return Place(
            id=v.text(d.get("id"), "id", max_len=80), name=name,
            city_id=v.text(d.get("city_id"), "city_id", max_len=40).lower(), categories=cats,
            setting=v.one_of(d.get("setting"), "setting", SETTINGS), is_demo=is_demo,
            description=v.text(d.get("description"), "description", max_len=400),
            map_link=v.https_url(d.get("map_link"), "map_link", required=False), hours=hours, hours_verified_at=hv,
            source_name=v.text(d.get("source_name"), "source_name", required=False),
            source_url=v.https_url(d.get("source_url"), "source_url", required=False),
            license_note=v.text(d.get("license_note"), "license_note", max_len=300, required=False),
            retrieved_at=v.aware_datetime(d.get("retrieved_at"), "retrieved_at", required=False),
            verified_by=v.text(d.get("verified_by"), "verified_by", required=False))

    def open_now(self, now: datetime) -> Optional[bool]:
        """True/False only when hours exist AND were verified within 30 days; otherwise None (unknown)."""
        if not self.hours or not self.hours_verified_at or now - self.hours_verified_at > HOURS_MAX_AGE:
            return None
        local = now.astimezone(ZoneInfo("Asia/Dubai"))
        for offset, day_dt in ((0, local), (1, local - timedelta(days=1))):
            for o, c in self.hours.get(DAYS[day_dt.weekday()], []):
                t = local.time()
                if c > o and offset == 0 and o <= t < c:
                    return True
                if c <= o and ((offset == 0 and t >= o) or (offset == 1 and t < c)):  # overnight range
                    return True
        return False

    def evidence(self, now_iso: str) -> Evidence:
        if self.is_demo:
            return Evidence("LUNARIS demo fixture", None, now_iso, None, "demo", "fictional placeholder entry",
                            ["Not a real venue.", "No hours, prices, sustainability labels or ratings."])
        return Evidence(self.source_name, self.source_url, iso_utc(self.retrieved_at),
                        iso_utc(self.hours_verified_at) if self.hours_verified_at else None, "verified",
                        f"curated entry, verified by {self.verified_by}; license: {self.license_note}",
                        ["Opening hours shown as open/closed only if verified within 30 days."])
