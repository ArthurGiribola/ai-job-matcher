import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def _get_secret(key: str) -> str:
    """Lê secret do ambiente ou do Streamlit secrets."""
    value = os.getenv(key, "")
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(key, "")
        except Exception:
            pass
    return value


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
    location_area = " ".join(raw.get("location", {}).get("area", [])).lower()
    text = f"{title} {description} {location} {location_area}".lower()
    is_remote = any(w in text for w in [
        "remote", "remoto", "home office", "anywhere", "hybrid",
        "work from home", "wfh", "fully remote", "100% remote",
        "distributed", "telecommut",
    ])
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


def fetch_remotive_jobs(
    keywords: str = "python",
    limit: int = 10,
) -> list[dict]:
    """
    Busca vagas remotas globais na Remotive API.
    Gratuita, sem autenticação necessária.
    """
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": keywords, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        jobs_raw = response.json().get("jobs", [])

        normalized = []
        for job in jobs_raw:
            title = job.get("title", "").strip()
            description = job.get("description", "").strip()
            company = job.get("company_name", "Company")
            url_job = job.get("url", "")

            normalized.append({
                "id": f"remotive_{job.get('id', '')}",
                "title": title,
                "company": company,
                "location": "Remote",
                "remote": True,
                "seniority": detect_seniority(title),
                "skills_required": extract_skills_from_text(f"{title} {description}"),
                "description": description[:2000],
                "posted_at": job.get("publication_date", datetime.today().strftime("%Y-%m-%d"))[:10],
                "source": "remotive",
                "url": url_job,
                "salary_min": 0,
                "salary_max": 0,
                "country": "remote",
            })

        print(f"Remotive: {len(normalized)} vagas encontradas.")
        return normalized
    except Exception as e:
        print(f"Erro Remotive: {e}")
        return []


def fetch_reed_jobs(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Busca vagas na Reed.co.uk — forte no mercado UK."""
    try:
        from requests.auth import HTTPBasicAuth
        api_key = _get_secret("REED_API_KEY")
        if not api_key:
            print("[Reed] API key não configurada — pulando")
            return []
        params = {
            "keywords": query,
            "locationName": location or "London",
            "resultsToTake": limit,
        }
        response = requests.get(
            "https://www.reed.co.uk/api/1.0/search",
            params=params,
            auth=HTTPBasicAuth(api_key, ""),
            timeout=10,
        )
        if response.status_code != 200:
            print(f"[Reed] Erro {response.status_code}")
            return []
        jobs = []
        for j in response.json().get("results", []):
            jobs.append({
                "id": f"reed_{j.get('jobId')}",
                "title": j.get("jobTitle", ""),
                "company": j.get("employerName", ""),
                "location": j.get("locationName", ""),
                "description": j.get("jobDescription", "")[:2000],
                "salary_min": j.get("minimumSalary") or 0,
                "salary_max": j.get("maximumSalary") or 0,
                "url": j.get("jobUrl", ""),
                "source": "reed",
                "country": "gb",
                "remote": False,
                "skills_required": [],
                "seniority": "mid",
                "posted_at": datetime.today().strftime("%Y-%m-%d"),
            })
        print(f"[Reed] {len(jobs)} vagas encontradas")
        return jobs
    except Exception as e:
        print(f"[Reed] Falhou: {e}")
        return []


def fetch_jooble_jobs(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Busca vagas no Jooble — agrega vagas do mundo todo."""
    try:
        api_key = _get_secret("JOOBLE_API_KEY")
        if not api_key:
            print("[Jooble] API key não configurada — pulando")
            return []
        payload = {
            "keywords": query,
            "location": location or "",
            "page": 1,
        }
        response = requests.post(
            f"https://jooble.org/api/{api_key}",
            json=payload,
            timeout=10,
        )
        if response.status_code != 200:
            print(f"[Jooble] Erro {response.status_code}")
            return []
        jobs = []
        for j in response.json().get("jobs", [])[:limit]:
            jobs.append({
                "id": f"jooble_{j.get('id', '')}",
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location", ""),
                "description": j.get("snippet", "")[:2000],
                "salary_min": 0,
                "salary_max": 0,
                "url": j.get("link", ""),
                "source": "jooble",
                "country": "us",
                "remote": "remote" in j.get("type", "").lower(),
                "skills_required": [],
                "seniority": "mid",
                "posted_at": datetime.today().strftime("%Y-%m-%d"),
            })
        print(f"[Jooble] {len(jobs)} vagas encontradas")
        return jobs
    except Exception as e:
        print(f"[Jooble] Falhou: {e}")
        return []


def fetch_muse_jobs(query: str, limit: int = 10) -> list[dict]:
    """Busca vagas na The Muse — gratuita, sem chave."""
    try:
        params = {"category": query, "page": 0}
        response = requests.get(
            "https://www.themuse.com/api/public/jobs",
            params=params,
            timeout=10,
        )
        if response.status_code != 200:
            print(f"[Muse] Erro {response.status_code}")
            return []
        jobs = []
        for j in response.json().get("results", [])[:limit]:
            locations = j.get("locations", [])
            location = locations[0].get("name", "Remote") if locations else "Remote"
            levels = j.get("levels", [])
            seniority = "junior" if any(
                "junior" in l.get("name", "").lower() or "entry" in l.get("name", "").lower()
                for l in levels
            ) else "mid"
            jobs.append({
                "id": f"muse_{j.get('id')}",
                "title": j.get("name", ""),
                "company": j.get("company", {}).get("name", ""),
                "location": location,
                "description": j.get("contents", "")[:2000],
                "salary_min": 0,
                "salary_max": 0,
                "url": j.get("refs", {}).get("landing_page", ""),
                "source": "muse",
                "country": "us",
                "remote": "remote" in location.lower() or "flexible" in location.lower(),
                "skills_required": [],
                "seniority": seniority,
                "posted_at": datetime.today().strftime("%Y-%m-%d"),
            })
        print(f"[Muse] {len(jobs)} vagas encontradas")
        return jobs
    except Exception as e:
        print(f"[Muse] Falhou: {e}")
        return []


def enrich_jobs_with_claude(jobs: list[dict], max_enrich: int = 10) -> list[dict]:
    """
    Enriquece skills das vagas usando Claude Haiku.
    Só processa vagas com descrição longa e poucas skills detectadas.
    Limita a max_enrich vagas para controlar custo.
    """
    enriched = 0
    for job in jobs:
        if enriched >= max_enrich:
            break
        skills = job.get("skills_required", [])
        description = job.get("description", "")
        if len(description) > 200 and len(skills) < 3:
            new_skills = extract_skills_with_ai(job.get("title", ""), description)
            if new_skills:
                job["skills_required"] = new_skills
                job["skills_enriched"] = True
                enriched += 1
                print(f"[Enrich] {job.get('title', '')[:40]} → {new_skills[:5]}")

    print(f"[Enrich] {enriched} vagas enriquecidas com Claude")
    return jobs


def get_jobs(
    candidate_skills: list[str] = None,
    limit: int = 20,
    country: str = "gb",
    location: str = "",
) -> list[dict]:
    cache_path = _DATA_DIR / f"jobs_cache_{country}.json"
    cache_meta_path = _DATA_DIR / f"jobs_cache_{country}_meta.json"

    if cache_path.exists() and cache_meta_path.exists():
        try:
            with open(cache_meta_path, "r") as f:
                meta = json.load(f)
            age_seconds = time.time() - meta.get("timestamp", 0)
            if age_seconds < 3600:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached:
                    print(f"Cache hit [{country}] — {len(cached)} vagas, {int(age_seconds)}s atrás")
                    return cached[:limit]
        except Exception:
            pass

    if candidate_skills:
        skill_query = " ".join(candidate_skills[:3])
    else:
        skill_query = "python developer"

    real_jobs = fetch_adzuna_jobs(
        keywords=skill_query,
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

    remotive_jobs = fetch_remotive_jobs(
        keywords=skill_query,
        limit=10,
    )

    mock_jobs = []
    if country == "br" and MOCK_PATH.exists():
        with open(MOCK_PATH, "r", encoding="utf-8") as f:
            mock_jobs = json.load(f)

    all_jobs = real_jobs + remotive_jobs + mock_jobs

    # Reed — só para UK
    if country == "gb":
        reed_jobs = fetch_reed_jobs(query=skill_query, location=location, limit=10)
        all_jobs.extend(reed_jobs)

    # Jooble — global
    jooble_jobs = fetch_jooble_jobs(query=skill_query, location=location, limit=10)
    all_jobs.extend(jooble_jobs)

    # The Muse — global, sem chave
    muse_jobs = fetch_muse_jobs(query=skill_query, limit=8)
    all_jobs.extend(muse_jobs)
    seen = set()
    unique = []
    for job in all_jobs:
        key = f"{job['title']}_{job['company']}".lower()
        if key not in seen:
            seen.add(key)
            unique.append(job)

    # Enriquece skills das vagas com Claude (só vagas com poucas skills)
    try:
        unique = enrich_jobs_with_claude(unique, max_enrich=8)
    except Exception as e:
        print(f"[Enrich] Falhou: {e}")

    cache_path = _DATA_DIR / f"jobs_cache_{country}.json"
    cache_meta_path = _DATA_DIR / f"jobs_cache_{country}_meta.json"
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(unique[:limit], f, ensure_ascii=False, indent=2)
    with open(cache_meta_path, "w") as f:
        json.dump({"timestamp": time.time(), "count": len(unique)}, f)

    return unique[:limit]
