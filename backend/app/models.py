from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

HouseSystem = Literal["P", "W", "K", "R", "C", "E"]
InterpretationStyle = Literal["modern", "traditional", "psychological"]
InterpretationFocus = Literal["general", "relationships", "career", "year_ahead"]
ReportKind = Literal["natal", "synastry", "composite", "astrocartography", "transits"]
ReportTier = Literal["free", "personalized", "deep"]


class BirthData(BaseModel):
    """Validated request model shared by chart and interpretation endpoints."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(default="", max_length=100)
    year: int = Field(ge=1, le=9999)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    tz_offset_hours: float = Field(default=3.0, ge=-14.0, le=14.0)
    house_system: HouseSystem = "P"
    style: InterpretationStyle = "modern"
    focus: InterpretationFocus = "general"
    time_unknown: bool = False
    timezone: str | None = Field(default=None, max_length=100)
    birthplace: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def validate_calendar_date(self) -> "BirthData":
        date(self.year, self.month, self.day)
        return self


class RelationshipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    person_a: BirthData
    person_b: BirthData
    style: InterpretationStyle = "modern"
    orb_profile: Literal["tight", "standard", "wide"] = "standard"


class TransitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birth: BirthData
    target_date: date | None = None
    style: InterpretationStyle = "modern"


class AccountRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=80)


class AccountLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class SavedChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(default="Saved chart", max_length=80)
    birth: BirthData


class ReportRequest(BaseModel):
    """Generic downloadable-report payload.

    `data` is the already-computed public response so report generation never
    silently recalculates with different settings. The backend sanitizes and
    limits text before rendering.
    """

    model_config = ConfigDict(extra="forbid")
    kind: ReportKind
    title: str = Field(default="AstroMYLA Report", max_length=160)
    data: dict
    interpretation: str = Field(default="", max_length=120_000)
    tier: ReportTier = "free"


class PremiumNatalReportRequest(BaseModel):
    """Server-side premium natal report request.

    Production access is protected by X-Premium-Token so a static frontend cannot
    bypass checkout simply by calling the report generator directly.
    """

    model_config = ConfigDict(extra="forbid")
    birth: BirthData
    tier: Literal["personalized", "deep"] = "personalized"
    questions: list[str] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_questions(self) -> "PremiumNatalReportRequest":
        cleaned: list[str] = []
        for q in self.questions:
            q2 = " ".join(str(q).split())[:500]
            if q2:
                cleaned.append(q2)
        self.questions = cleaned[:3]
        return self


class CheckoutBuyer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    phone: str = Field(min_length=7, max_length=32)
    identity_number: str = Field(min_length=5, max_length=32)
    address: str = Field(min_length=5, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    country: str = Field(default="Turkey", min_length=2, max_length=100)


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product: Literal["personalized_reading", "deep_reading"]
    buyer: CheckoutBuyer
    birth: BirthData
    questions: list[str] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def clean_checkout_questions(self) -> "CheckoutRequest":
        self.questions = [" ".join(str(q).split())[:500] for q in self.questions if " ".join(str(q).split())][:3]
        return self
