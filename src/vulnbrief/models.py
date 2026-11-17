"""Contracts for model output, tools and source evidence."""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CVE_PATTERN = r"^CVE-\d{4}-\d{4,19}$"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Plan(StrictModel):
    objective: str
    steps: list[str] = Field(min_length=1, max_length=6)
    assumptions: list[str]


class Asset(StrictModel):
    label: str = Field(max_length=120)
    cve_id: str = Field(pattern=CVE_PATTERN)
    exposure: str = Field(max_length=160)
    business_importance: str = Field(max_length=160)
    product_version: str | None = Field(default=None, max_length=160)
    product: str | None = Field(default=None, max_length=160)
    owner: str | None = Field(default=None, max_length=120)


class Context(StrictModel):
    origin: Literal["synthetic", "user_supplied"]
    notes: str = Field(max_length=1000)
    assets: list[Asset] = Field(min_length=1, max_length=12)

    @field_validator("assets")
    @classmethod
    def limit_scope(cls, assets):
        if len({a.cve_id for a in assets}) > 3:
            raise ValueError("At most three distinct CVEs per run")
        if len({(a.label,a.cve_id) for a in assets}) != len(assets):
            raise ValueError("Each asset label and CVE pair must be unique")
        return assets


class NoArgs(StrictModel):
    pass


class CveArgs(StrictModel):
    cve_id: str = Field(pattern=CVE_PATTERN)
    source: Literal["primary", "official_mirror"]


class CvesArgs(StrictModel):
    cve_ids: list[str] = Field(min_length=1, max_length=3)

    @field_validator("cve_ids")
    @classmethod
    def validate_cves(cls, values):
        import re
        if any(not re.fullmatch(CVE_PATTERN, v) for v in values):
            raise ValueError("Invalid CVE identifier")
        return list(dict.fromkeys(values))


class KevArgs(CvesArgs):
    source: Literal["primary", "official_mirror"]


class Evidence(StrictModel):
    evidence_id: str
    tool: str
    cve_ids: list[str]
    source_url: str
    retrieved_at: str
    source_date: str | None
    location: str
    data: dict


class Claim(StrictModel):
    text: str
    evidence_ids: list[str] = Field(min_length=1)
    field_refs: list["SourceRef"] = Field(min_length=1)


class SourceRef(StrictModel):
    evidence_id: str = Field(pattern=r"^E[0-9]{3,}$")
    field_path: str = Field(description="JSON pointer into evidence.data, e.g. /results/0/score", pattern=r"^/")


class RecommendedAction(StrictModel):
    text: str
    applies_when: str = Field(description="Explicit prerequisites: verify asset version/configuration before any change")
    support: list[SourceRef] = Field(min_length=1)


class Finding(StrictModel):
    cve_id: str = Field(pattern=CVE_PATTERN)
    rank: int = Field(ge=1, le=3)
    priority: Literal["high", "medium", "low", "needs_review"]
    rationale: str
    evidence_ids: list[str] = Field(min_length=1)
    recommended_actions: list[RecommendedAction] = Field(min_length=1)
    uncertainties: list[str]


class ReportDraft(StrictModel):
    status: Literal["complete", "partial"]
    summary: list[Claim] = Field(min_length=1)
    findings: list[Finding] = Field(min_length=1, max_length=3)
    limitations: list[str]


class ReportReview(StrictModel):
    accepted: bool
    issues: list[str]
