import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.scoring_engine import rank_jobs, get_top_missing_skills

app = FastAPI(
    title="AI Job Matcher",
    description="API que analisa skills e ranqueia vagas por compatibilidade técnica.",
    version="1.0.0",
)

JOBS_PATH = Path(__file__).parent.parent / "data" / "mock_jobs.json"

def load_jobs() -> list[dict]:
    if not JOBS_PATH.exists():
        return []
    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

JOBS = load_jobs()


class Filters(BaseModel):
    remote: Optional[bool] = Field(None)
    seniority: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    min_salary: Optional[int] = Field(None)


class MatchRequest(BaseModel):
    skills: list[str] = Field(..., example=["Python", "FastAPI", "Machine Learning", "AWS"])
    seniority: str = Field(default="junior")
    filters: Optional[Filters] = Field(default=None)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1, le=50)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "message": "AI Job Matcher rodando!",
        "docs": "/docs",
        "jobs_loaded": len(JOBS),
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "jobs_in_memory": len(JOBS)}


@app.get("/jobs", tags=["Jobs"])
def list_jobs(limit: int = 20):
    return {"total": len(JOBS), "jobs": JOBS[:limit]}


@app.post("/match", tags=["Matching"])
def match_jobs(request: MatchRequest):
    if not JOBS:
        raise HTTPException(status_code=503, detail="Nenhuma vaga disponível.")
    if not request.skills:
        raise HTTPException(status_code=400, detail="Informe ao menos uma skill.")
    filters = request.filters.model_dump() if request.filters else {}
    ranked = rank_jobs(
        jobs=JOBS,
        candidate_skills=request.skills,
        candidate_seniority=request.seniority,
        filters=filters,
        min_score=request.min_score,
        limit=request.limit,
    )
    return {
        "total_jobs_analyzed": len(JOBS),
        "total_matches": len(ranked),
        "candidate": {"skills": request.skills, "seniority": request.seniority},
        "results": ranked,
        "top_missing_skills": get_top_missing_skills(ranked),
    }


@app.post("/match/quick", tags=["Matching"])
def quick_match(skills: list[str]):
    if not skills:
        raise HTTPException(status_code=400, detail="Informe ao menos uma skill.")
    ranked = rank_jobs(jobs=JOBS, candidate_skills=skills, limit=5)
    return {
        "top_5_jobs": ranked,
        "top_missing_skills": get_top_missing_skills(ranked),
    }