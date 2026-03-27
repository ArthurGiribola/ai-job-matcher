import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.job import Job

router = APIRouter(prefix="/jobs", tags=["Jobs"])

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "mock_jobs.json"


def load_jobs() -> list[Job]:
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Job(**item) for item in raw]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Arquivo mock_jobs.json não encontrado") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="mock_jobs.json está inválido") from exc


@router.get("/search", response_model=list[Job])
def search_jobs():
    return load_jobs()


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    jobs = load_jobs()
    for job in jobs:
        if job.id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Vaga não encontrada")


@router.post("/collect")
def collect_jobs():
    jobs = load_jobs()
    return {
        "message": "Coleta mock executada com sucesso",
        "total_collected": len(jobs),
    }