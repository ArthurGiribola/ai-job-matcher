from typing import Literal

from pydantic import BaseModel, Field

from app.models.job import Job


class MatchFilters(BaseModel):
    title: str | None = None
    location: str | None = None
    remote: bool | None = None
    seniority: Literal["junior", "mid", "senior", "lead", "any"] | None = None
    stack: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    resume_id: str | None = None
    filters: MatchFilters = Field(default_factory=MatchFilters)
    limit: int = 20
    min_score: float = 0.4


class MatchResult(BaseModel):
    job: Job
    score: float
    reason: str
    gaps: list[str]
    highlight_skills: list[str]


class MatchResponse(BaseModel):
    total: int
    results: list[MatchResult]
    top_missing_skills: list[str]