from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    remote: bool
    seniority: Literal["junior", "mid", "senior", "lead", "any"]
    skills_required: list[str]
    description: str
    posted_at: datetime
    source: str
    url: str
    salary_range: tuple[int, int] | None = None