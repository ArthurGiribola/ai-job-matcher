import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock_jobs.json"
CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "jobs_cache.json"

SKILL_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "FastAPI", "Django", "Flask", "Node.js", "Docker", "Kubernetes", "AWS",
    "GCP", "Azure", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQL",
    "Machine Learning", "Deep Learning", "NLP", "scikit-learn", "TensorFlow",
    "PyTorch", "pandas", "NumPy", "Git", "CI/CD", "Terraform", "Linux",
    "REST API", "GraphQL", "Microservices", "Spark", "Airflow", "MLflow",
    "LangChain", "LLM", "HuggingFace", "Power BI", "Tableau", "C++",
    "Statistics", "Probability", "Linear Algebra",
]


def extract_skills_from_text(text: str) -> list[str]:
    """Extrai skills de um texto usando lista de palavras-chave."""
    text_lower = text.lower()
    return [s for s in SKILL_KEYWORDS if s.lower() in text_lower]


def detect_seniority(title: str) -> str:
    """Detecta senioridade pelo título da vaga."""
    title_lower = title.lower()
    if any(w in title_lower for w in ["senior", "sr.", "lead", "principal", "staff"]):
        return "senior"
    if any(w in title_lower for w in ["junior", "jr.", "intern", "entry", "graduate"]):
        return "junior"
    if any(w in title_lower for w in ["mid", "pleno", "intermediate"]):
        return "mid"
    return "mid"


def normalize_job(raw: dict) -> dict:
    """Converte vaga da Adzuna para o schema padrão do sistema."""
    title = raw.get("title", "").strip()
    description = raw.get("description", "").strip()
    company = raw.get("company", {}).get("display_name", "Company")
    location = raw.get("location", {}).get("display_name", "Remote")
    url = raw.get("redirect_url", "")
    salary_min = int(raw.get("salary_min") or 0)
    salary_max = int(raw.get("salary_max") or 0)

    text = f"{title} {description}".lower()
    is_remote = any(w in text for w in ["remote", "remoto", "home office", "anywhere", "hybrid"])

    try:
        posted_at = datetime.fromisoformat(
            raw.get("created", "")[:10]
        ).strftime("%Y-%m-%d")
    except Exception:
        posted_at = datetime.today().strftime("%Y-%m-%d")

    return {
        "id": f"adzuna_{raw.get('id', '')}",
        "title": title,
        "company": company,
        "location": location,
        "remote": is_remote,
        "seniority": detect_seniority(title),
        "skills_required": extract_skills_from_text(f"{title} {description}"),
        "description": description[:500],
        "posted_at": posted_at,
        "source": "adzuna",
        "url": url,
        "salary_min": salary_min,
        "salary_max": salary_max,
    }


def fetch_adzuna_jobs(
    keywords: str = "python developer",
    location: str = "london",
    results_per_page: int = 20,
    page: int = 1,
) -> list[dict]:
    """
    Busca vagas reais da Adzuna API (país GB — maior base de dados).
    Retorna lista normalizada no schema padrão.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("Credenciais Adzuna não encontradas.")
        return []

    url = f"{ADZUNA_BASE_URL}/gb/search/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": keywords,
        "where": location,
        "content-type": "application/json",
        "sort_by": "date",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        jobs = [normalize_job(r) for r in results]
        print(f"Adzuna: {len(jobs)} vagas encontradas.")
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"Erro Adzuna: {e}")
        return []
    
def get_jobs(
    candidate_skills: list[str] = None,
    limit: int = 20,
    country: str = "gb",
    location: str = "",
) -> list[dict]:
    """
    Retorna vagas combinando Adzuna + mock jobs.
    Adzuna primeiro, mock como fallback/complemento.
    """
    if candidate_skills:
        query = " ".join(candidate_skills[:3])
    else:
        query = "python developer"

    where = location if location else country
    real_jobs = fetch_adzuna_jobs(
        keywords=query,
        location=where,
        results_per_page=limit,
    )

    mock_jobs = []
    if MOCK_PATH.exists():
        with open(MOCK_PATH, "r", encoding="utf-8") as f:
            mock_jobs = json.load(f)

    all_jobs = real_jobs + mock_jobs

    seen = set()
    unique = []
    for job in all_jobs:
        key = f"{job['title']}_{job['company']}".lower()
        if key not in seen:
            seen.add(key)
            unique.append(job)

    CACHE_PATH.parent.mkdir(exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(unique[:limit], f, ensure_ascii=False, indent=2)

    return unique[:limit]