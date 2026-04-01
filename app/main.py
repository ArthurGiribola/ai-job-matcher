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

from app.services.job_collector import get_jobs

def load_jobs() -> list[dict]:
    try:
        jobs = get_jobs(limit=40)
        if jobs:
            return jobs
    except Exception as e:
        print(f"Erro ao carregar vagas: {e}")
    # Fallback para mock
    mock_path = Path(__file__).parent.parent / "data" / "mock_jobs.json"
    if mock_path.exists():
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

JOBS = load_jobs()\

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
from app.services.resume_parser import parse_resume_text, parse_resume_pdf
from fastapi import UploadFile, File
import tempfile
import os


@app.post("/resume/analyze-text", tags=["Resume"])
def analyze_resume_text(text: str):
    """
    Analisa texto do currículo e retorna perfil estruturado.
    Cole o texto do currículo diretamente.
    """
    if not text or len(text) < 50:
        raise HTTPException(status_code=400, detail="Texto muito curto. Cole o conteúdo completo do currículo.")
    profile = parse_resume_text(text)
    return {
        "profile": profile,
        "message": f"Encontradas {profile['total_skills']} skills. Nível detectado: {profile['seniority']}."
    }


@app.post("/resume/upload", tags=["Resume"])
async def upload_resume(file: UploadFile = File(...)):
    """
    Faz upload de currículo em PDF e retorna perfil estruturado.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        profile = parse_resume_pdf(tmp_path)
        return {
            "profile": profile,
            "message": f"Currículo processado. Encontradas {profile.get('total_skills', 0)} skills."
        }
    finally:
        os.unlink(tmp_path)


@app.post("/resume/analyze-and-match", tags=["Resume"])
def analyze_and_match(text: str, seniority: str = "junior"):
    """
    Analisa o currículo E já retorna as vagas ranqueadas.
    Tudo em uma chamada só.
    """
    if not text or len(text) < 50:
        raise HTTPException(status_code=400, detail="Texto muito curto.")
    profile = parse_resume_text(text)
    ranked = rank_jobs(
        jobs=JOBS,
        candidate_skills=profile["skills"],
        candidate_seniority=profile.get("seniority", seniority),
        limit=10,
    )
    return {
        "profile": profile,
        "total_jobs_analyzed": len(JOBS),
        "total_matches": len(ranked),
        "results": ranked,
        "top_missing_skills": get_top_missing_skills(ranked),
    }