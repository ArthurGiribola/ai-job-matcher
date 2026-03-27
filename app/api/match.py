import json
from pathlib import Path

from fastapi import APIRouter

from app.models.job import Job
from app.models.match import MatchRequest, MatchResponse, MatchResult
from app.services.scoring_engine import aggregate_missing_skills, final_score
from app.services.skill_extractor import extract_skills_from_text

router = APIRouter(prefix="/match", tags=["Match"])

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "mock_jobs.json"


def load_jobs():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Job(**item) for item in raw]


@router.post("/", response_model=MatchResponse)
def match(payload: MatchRequest):
    jobs = load_jobs()

    # 🔥 TEXTO + STACK
    text = getattr(payload, "text", "")

    extracted = extract_skills_from_text(text) if text else []
    manual = payload.filters.stack or []

    cv_skills = list(set(extracted + manual))

    cv_seniority = payload.filters.seniority or "any"

    scored = []
    for job in jobs:
        result = final_score(cv_skills, cv_seniority, job, payload.filters)

        if result["score"] >= payload.min_score:
            scored.append(
                MatchResult(
                    job=job,
                    score=result["score"],
                    reason=result["reason"],
                    gaps=result["gaps"],
                    highlight_skills=result["highlight_skills"],
                )
            )

    scored.sort(key=lambda x: x.score, reverse=True)

    limited = scored[: payload.limit]

    top_missing_skills = aggregate_missing_skills(
        [{"gaps": item.gaps} for item in limited]
    )

    return MatchResponse(
        total=len(scored),
        results=limited,
        top_missing_skills=top_missing_skills,
    )


@router.get("/{job_id}/gaps")
def get_match_gaps(job_id: str):
    jobs = load_jobs()

    for job in jobs:
        if job.id == job_id:
            return {
                "job_id": job_id,
                "gaps": job.skills_required
            }

    return {"job_id": job_id, "gaps": []}