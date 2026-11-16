"""Enumerations mirrored from contracts/data-models.json (and DATA_AND_EVIDENCE.md).

Stdlib-only on purpose. tests/core/test_contract_enums.py compares every value
here against the contract file, so drift fails CI.
"""
from typing import Literal, get_args

# --- contracts/data-models.json -------------------------------------------
DataStatus = Literal["live", "historical", "modeled", "demo", "self_reported", "verified"]
SupportStatus = Literal["supported", "preview", "unsupported"]
HeatCaution = Literal["low", "moderate", "elevated", "unknown"]
ComparisonType = Literal["travel", "food", "energy", "business"]
MissionStatus = Literal["demo", "proposed", "reviewing", "approved", "active", "complete"]
PermissionStatus = Literal["unknown", "pending", "approved"]
MissionVerificationStatus = Literal["unverified", "self_reported", "reviewed", "verified"]
ImpactVerificationStatus = Literal["self_reported", "reviewed", "verified"]

# --- DATA_AND_EVIDENCE.md item 11 (NOT in data-models.json; see handoff) ----
BusinessDisclosureStatus = Literal["self_reported", "documentation_reviewed", "independently_verified"]

# --- API-level (not contract) ----------------------------------------------
SourceState = Literal["available", "stale", "unavailable", "not_integrated", "demo"]

DATA_STATUSES = frozenset(get_args(DataStatus))
SUPPORT_STATUSES = frozenset(get_args(SupportStatus))
HEAT_CAUTIONS = frozenset(get_args(HeatCaution))
COMPARISON_TYPES = frozenset(get_args(ComparisonType))
MISSION_STATUSES = frozenset(get_args(MissionStatus))
PERMISSION_STATUSES = frozenset(get_args(PermissionStatus))
MISSION_VERIFICATION_STATUSES = frozenset(get_args(MissionVerificationStatus))
IMPACT_VERIFICATION_STATUSES = frozenset(get_args(ImpactVerificationStatus))
BUSINESS_DISCLOSURE_STATUSES = frozenset(get_args(BusinessDisclosureStatus))
SOURCE_STATES = frozenset(get_args(SourceState))

# MVP: only first two business disclosure levels are supported (DATA_AND_EVIDENCE.md #11).
BUSINESS_DISCLOSURE_MVP = frozenset({"self_reported", "documentation_reviewed"})

# Which Evidence.data_status values each surface may legitimately emit. A provider
# returning anything else is a contract violation (HTTP 502), never passed through.
WEATHER_ALLOWED_DATA_STATUS = frozenset({"live", "historical", "modeled", "demo"})
WINDOW_ALLOWED_DATA_STATUS = frozenset({"live", "modeled", "demo"})
# Choice factors are published/modeled estimates; nothing here can be "self_reported" or "verified".
CHOICES_ALLOWED_DATA_STATUS = frozenset({"live", "historical", "modeled", "demo"})

# Preference vocabularies inferred from PRODUCT_BRIEF.md journey 2 (confirm with Codex/lead).
WEATHER_MOODS = ("rainy_cozy", "cloudy_moody", "sunny", "breezy", "misty", "after_dark")
ACTIVITIES = ("cafes", "walking", "exercise", "culture", "indoor")
