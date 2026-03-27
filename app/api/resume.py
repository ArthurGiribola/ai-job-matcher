from fastapi import APIRouter

from app.services.skill_extractor import extract_skills_from_text

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/parse-text")
def parse_resume_text(payload: dict):
    text = payload.get("text", "")

    skills = extract_skills_from_text(text)

    return {
        "skills": skills,
        "total_skills": len(skills)
    }