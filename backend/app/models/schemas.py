from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field

IssueStatus = Literal["fail", "warn", "pass"]
CategoryKey = Literal["parseability_format", "layout_structure", "content_completeness", "keyword_match"]


class Issue(BaseModel):
    id: str
    category: CategoryKey
    check: str
    status: IssueStatus
    title: str
    detail: str
    fix: str = ""
    weight: float
    score: float


class CategoryScore(BaseModel):
    key: CategoryKey
    label: str
    weight: float
    score: float
    issues: list[Issue]


class RubricInfo(BaseModel):
    base_weights: dict[str, float]
    applied_weights: dict[str, float]
    jd_provided: bool
    note: str


class KeywordDetails(BaseModel):
    matched: list[str]
    missing: list[str]
    hard_skills_matched: list[str]
    hard_skills_missing: list[str]


class CheckResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filename: str
    jd_provided: bool
    overall_score: int
    categories: list[CategoryScore]
    rubric: RubricInfo
    jd_text: str | None = None
    email: str | None = None
    keyword_details: KeywordDetails | None = None


class EmailCaptureRequest(BaseModel):
    email: EmailStr
