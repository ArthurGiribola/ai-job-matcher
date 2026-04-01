import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def _get_adzuna_credentials() -> tuple[str | None, str | None]:
    """Lê credenciais Adzuna do .env ou st.secrets (lazy, para Streamlit Cloud)."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        try:
            import streamlit as st
            app_id = app_id or st.secrets.get("ADZUNA_APP_ID")
            app_key = app_key or st.secrets.get("ADZUNA_APP_KEY")
        except Exception:
            pass
    return app_id, app_key

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock_jobs.json"
_DATA_DIR = Path(__file__).parent.parent.parent / "data"

SUPPORTED_COUNTRIES = {
    "gb": "Reino Unido",
    "us": "Estados Unidos",
    "au": "Austrália",
    "ca": "Canadá",
    "de": "Alemanha",
    "fr": "França",
    "nl": "Países Baixos",
    "sg": "Singapura",
    "nz": "Nova Zelândia",
    "za": "África do Sul",
    "in": "Índia",
    "at": "Áustria",
    "be": "Bélgica",
    "br": "Brasil",
    "mx": "México",
    "it": "Itália",
    "es": "Espanha",
    "pl": "Polônia",
    "ru": "Rússia",
    "ch": "Suíça",
}

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
    text_lower = text.lower()
    return [s for s in SKILL_KEYWORDS if s.lower() in text_lower]


def extract_skills_with_ai(title: str, description: str) -> list[str]:
    """
    Extrai skills da vaga usando Claude Haiku.
    Fallback para keyword matching se Claude não estiver disponível.
    """
    try:
        import anthropic
        from app.services.resume_analyzer import _get_api_key
        api_key = _get_api_key()
        if not api_key:
            return extract_skills_from_text(f"{title} {description}")

        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Extract the technical skills required for this job.
Return ONLY a JSON array of skill names, nothing else.
Example: ["Python", "Docker", "PostgreSQL"]

Job title: {title}
Job description: {description[:1000]}"""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        import json
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        skills = json.loads(raw)
        if isinstance(skills, list):
            return skills[:15]
    except Exception as e:
        print(f"AI skill extraction failed, using keywords: {e}")

    return extract_skills_from_text(f"{title} {description}")


def detect_seniority(title: str) -> str:
    title_lower = title.lower()
    if any(w in title_lower for w in ["senior", "sr.", "lead", "principal", "staff"]):
        return "senior"
    if any(w in title_lower for w in ["junior", "jr.", "intern", "entry", "graduate"]):
        return "junior"
    if any(w in title_lower for w in ["mid", "pleno", "intermediate"]):
        return "mid"
    return "mid"


def normalize_job(raw: dict, country_code: str = "gb") -> dict:
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
        posted_at = datetime.fromisoformat(raw.get("created", "")[:10]).strftime("%Y-%m-%d")
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
        "description": description[:2000],
        "posted_at": posted_at,
        "source": "adzuna",
        "url": url,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "country": country_code,
    }


def fetch_adzuna_jobs(
    keywords: str = "python developer",
    location: str = "",
    results_per_page: int = 20,
    page: int = 1,
    country_code: str = "gb",
) -> list[dict]:
    app_id, app_key = _get_adzuna_credentials()
    if not app_id or not app_key:
        print("Credenciais Adzuna não encontradas.")
        return []

    if country_code not in SUPPORTED_COUNTRIES:
        country_code = "gb"

    url = f"{ADZUNA_BASE_URL}/{country_code}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": keywords,
        "content-type": "application/json",
        "sort_by": "date",
    }
    if location:
        params["where"] = location

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        jobs = [normalize_job(r, country_code) for r in results]
        print(f"Adzuna [{country_code}]: {len(jobs)} vagas encontradas.")
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
    if candidate_skills:
        query = " ".join(candidate_skills[:3])
    else:
        query = "python developer"

    real_jobs = fetch_adzuna_jobs(
        keywords=query,
        location=location,
        results_per_page=limit,
        country_code=country,
    )

    if not real_jobs:
        real_jobs = fetch_adzuna_jobs(
            keywords="python developer",
            location=location,
            results_per_page=limit,
            country_code=country,
        )

    mock_jobs = []
    if country == "br" and MOCK_PATH.exists():
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

    cache_path = _DATA_DIR / f"jobs_cache_{country}.json"
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(unique[:limit], f, ensure_ascii=False, indent=2)

    return unique[:limit]
