"""Pydantic models. Contract models mirror contracts/data-models.json; additions are marked."""
from __future__ import annotations

from datetime import timezone
from typing import Annotated, Any

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import (
    ACTIVITIES,
    WEATHER_MOODS,
    BusinessDisclosureStatus,
    ComparisonType,
    DataStatus,
    HeatCaution,
    ImpactVerificationStatus,
    MissionStatus,
    MissionVerificationStatus,
    PermissionStatus,
    SourceState,
    SupportStatus,
)

# All timestamps are normalised to UTC internally; the product layer displays Asia/Dubai.
UTCDatetime = Annotated[AwareDatetime, AfterValidator(lambda d: d.astimezone(timezone.utc))]
Slug = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")]

STRICT = ConfigDict(extra="forbid")


# ---- Evidence (contract) + optional provenance fields from DATA_AND_EVIDENCE.md ----------
class Evidence(BaseModel):
    model_config = STRICT
    source_name: str = Field(min_length=1, max_length=300)
    source_url: str | None = Field(default=None, max_length=2000)
    retrieved_at: UTCDatetime
    valid_at: UTCDatetime | None = None
    data_status: DataStatus
    method: str = Field(min_length=1, max_length=2000)
    limitations: list[str]
    # Additive, optional (NOT in data-models.json v0.1.0; see handoff "contract gaps"):
    license_note: str | None = None
    location_precision: str | None = None
    model_id: str | None = None
    assumptions: list[str] | None = None
    uncertainty: str | dict[str, Any] | None = None


class SourceStatus(BaseModel):
    """Standardised source status attached to every upstream-backed response (API-level addition)."""
    state: SourceState
    detail: str | None = None
    checked_at: UTCDatetime


class ErrorDetail(BaseModel):
    loc: list[str] = []
    msg: str
    type: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list[ErrorDetail] = []


class ErrorResponse(BaseModel):
    error: ErrorBody


# ---- Cities ----------------------------------------------------------------------------
class City(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    country_code: str
    timezone: str
    support_status: SupportStatus
    center_lat: float
    center_lon: float


class CityList(BaseModel):
    cities: list[City]


# ---- Session (guest) ---------------------------------------------------------------------
class SessionCreated(BaseModel):
    session_token: str
    token_type: str = "bearer"
    expires_at: UTCDatetime
    user_id: str
    auth_mode: str
    notice: str


class SessionInfo(BaseModel):
    user_id: str
    auth_mode: str
    expires_at: UTCDatetime
    notice: str


# ---- Preferences -------------------------------------------------------------------------
class UserPreferences(BaseModel):
    """Contract shape. Comfort temperatures are personal preferences, NOT medical safety thresholds."""
    model_config = STRICT
    user_id: str | None = None
    city_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    weather_moods: list[str] = Field(default_factory=list, max_length=len(WEATHER_MOODS))
    comfort_min_c: float = Field(ge=-10, le=55)
    comfort_max_c: float = Field(ge=-10, le=55)
    activities: list[str] = Field(default_factory=list, max_length=len(ACTIVITIES))
    priorities: list[Slug] = Field(default_factory=list, max_length=10)
    notification_consent: bool

    @field_validator("weather_moods")
    @classmethod
    def _moods(cls, v: list[str]) -> list[str]:
        bad = sorted(set(v) - set(WEATHER_MOODS))
        if bad:
            raise ValueError(f"unknown weather_moods {bad}; allowed: {list(WEATHER_MOODS)}")
        return list(dict.fromkeys(v))

    @field_validator("activities")
    @classmethod
    def _acts(cls, v: list[str]) -> list[str]:
        bad = sorted(set(v) - set(ACTIVITIES))
        if bad:
            raise ValueError(f"unknown activities {bad}; allowed: {list(ACTIVITIES)}")
        return list(dict.fromkeys(v))

    @field_validator("priorities")
    @classmethod
    def _prios(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))

    @model_validator(mode="after")
    def _range(self) -> "UserPreferences":
        if self.comfort_min_c >= self.comfort_max_c:
            raise ValueError("comfort_min_c must be lower than comfort_max_c")
        return self


class PreferencesResponse(BaseModel):
    preferences: UserPreferences | None
    persisted: bool
    notice: str


# ---- Weather -----------------------------------------------------------------------------
class HourConditions(BaseModel):
    model_config = STRICT
    timestamp: UTCDatetime
    temperature_c: float | None = None
    apparent_temperature_c: float | None = None
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    precip_probability_percent: float | None = Field(default=None, ge=0, le=100)
    weather_code: int | None = None
    is_day: bool | None = None
    evidence: Evidence


class CacheInfo(BaseModel):
    served_from_cache: bool
    age_seconds: float


class WeatherResponse(BaseModel):
    city_id: str
    timezone: str
    location_precision: str
    horizon_hours: int
    hours: list[HourConditions]
    source_status: SourceStatus
    cache: CacheInfo
    notice: str


# ---- HeatShield --------------------------------------------------------------------------
class LocationInput(BaseModel):
    """Optional opt-in location. Coarsened to ~1 km and never stored or logged."""
    model_config = STRICT
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    consent: bool


class HeatShieldRequest(BaseModel):
    model_config = STRICT
    city_id: str = Field(default="dubai", pattern=r"^[a-z0-9-]+$", max_length=64)
    activity: Slug
    horizon_hours: int = Field(default=24, ge=1, le=120)
    window_minutes: int = Field(default=60, ge=30, le=240)
    max_windows: int = Field(default=5, ge=1, le=20)
    comfort_min_c: float | None = Field(default=None, ge=-10, le=55)
    comfort_max_c: float | None = Field(default=None, ge=-10, le=55)
    location: LocationInput | None = None

    @model_validator(mode="after")
    def _comfort(self) -> "HeatShieldRequest":
        a, b = self.comfort_min_c, self.comfort_max_c
        if (a is None) != (b is None):
            raise ValueError("provide both comfort_min_c and comfort_max_c, or neither (saved preferences are used)")
        if a is not None and b is not None and a >= b:
            raise ValueError("comfort_min_c must be lower than comfort_max_c")
        return self


class ActivityWindow(BaseModel):
    model_config = STRICT
    start: UTCDatetime
    end: UTCDatetime
    comfort_rank: int = Field(ge=1)
    heat_caution: HeatCaution
    reason_codes: list[str]
    evidence: Evidence

    @model_validator(mode="after")
    def _order(self) -> "ActivityWindow":
        if self.end <= self.start:
            raise ValueError("window end must be after start")
        return self


class HeatShieldResponse(BaseModel):
    city_id: str
    activity: str
    windows: list[ActivityWindow]
    comfort_range_c: tuple[float, float]
    source_status: SourceStatus
    notices: list[str]


# ---- Choices (contract: ChoiceComparison) --------------------------------------------------
class ChoiceComparison(BaseModel):
    model_config = STRICT
    choice_id: str = Field(min_length=1)
    comparison_type: ComparisonType
    alternatives: list[dict[str, Any]]
    estimated_impacts: list[dict[str, Any]]
    assumptions: list[str]
    evidence: list[Evidence] = Field(min_length=1)


# ---- Places / business evidence (shapes beyond `id` + evidence are provider-defined) -------
class PlaceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    data_status: DataStatus
    evidence: list[Evidence] = Field(min_length=1)


class PlaceList(BaseModel):
    places: list[PlaceRecord]
    source_status: SourceStatus


class BusinessEvidenceProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    disclosure_status: BusinessDisclosureStatus
    evidence: list[Evidence] = Field(min_length=1)
    notice: str = "Self-reported or documentation-reviewed claims only. This is not a certification."


# ---- Missions ----------------------------------------------------------------------------
class CommunityMission(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    city_id: str
    status: MissionStatus
    permission_status: PermissionStatus
    verification_status: MissionVerificationStatus
    organizer_id: str | None = None
    summary: str | None = None  # additive


class MissionList(BaseModel):
    missions: list[CommunityMission]
    source_status: SourceStatus


class MissionInterestRequest(BaseModel):
    model_config = STRICT
    consent: bool


class MissionInterestStored(BaseModel):
    interest_id: str
    mission_id: str
    mission_status: MissionStatus
    status: str = "interest_recorded"
    registration_confirmed: bool = False
    created_at: UTCDatetime
    notice: str


# ---- Impact ------------------------------------------------------------------------------
class ImpactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: str
    user_id: str
    action_type: str
    verification_status: ImpactVerificationStatus
    impact_estimate: dict[str, Any] | None = None
    evidence: list[Evidence]


class ImpactList(BaseModel):
    records: list[ImpactRecord]
    verification_counts: dict[str, int]
    notice: str
