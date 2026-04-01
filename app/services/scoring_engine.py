from datetime import date, datetime
from typing import Optional

HIGH_VALUE_SKILLS = {
    "LLM": 0.05, "LangChain": 0.04, "MLflow": 0.04,
    "Kubernetes": 0.03, "Terraform": 0.03, "AWS": 0.03,
    "GCP": 0.03, "Azure": 0.03, "Machine Learning": 0.03,
    "Docker": 0.02, "FastAPI": 0.02, "Python": 0.02,
    "Vector Databases": 0.04, "HuggingFace": 0.03, "NLP": 0.03,
}

SENIORITY_LEVELS = {"junior": 1, "mid": 2, "senior": 3, "lead": 4, "any": 0}


def normalize_skills(skills: list[str]) -> set[str]:
    return {s.strip().lower() for s in skills if s.strip()}


def skill_score(
    candidate_skills: list[str],
    job_skills: list[str],
    resume_text: str = "",
    job: dict = None,
) -> float:
    """
    Calcula compatibilidade de skills.
    
    Se resume_text e job forem fornecidos: usa embeddings semânticos (real AI).
    Caso contrário: usa Jaccard como fallback (keyword matching).
    """
    # Caminho semântico — embedding real
    if resume_text and job:
        try:
            from app.services.embedder import resume_job_similarity
            semantic = resume_job_similarity(resume_text, job)
            return min(1.0, semantic)
        except Exception as e:
            print(f"Embedding falhou, usando Jaccard: {e}")

    # Fallback — Jaccard
    if not job_skills:
        return 0.5
    cv_set = normalize_skills(candidate_skills)
    job_set = normalize_skills(job_skills)
    intersection = cv_set & job_set
    union = cv_set | job_set
    if not union:
        return 0.0
    jaccard = len(intersection) / len(union)
    must_have = normalize_skills(job_skills[:3])
    bonus = len(cv_set & must_have) * 0.04
    return min(1.0, jaccard + bonus)


def seniority_score(candidate_level: str, job_level: str) -> float:
    if job_level == "any":
        return 1.0
    cv_level = SENIORITY_LEVELS.get(candidate_level.lower(), 1)
    jb_level = SENIORITY_LEVELS.get(job_level.lower(), 1)
    diff = abs(cv_level - jb_level)
    return {0: 1.0, 1: 0.7, 2: 0.3, 3: 0.0}.get(diff, 0.0)


def recency_score(posted_at: str) -> float:
    try:
        posted_date = datetime.strptime(posted_at, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 0.5
    days_old = (date.today() - posted_date).days
    if days_old <= 3:   return 1.0
    elif days_old <= 7:  return 0.9
    elif days_old <= 14: return 0.75
    elif days_old <= 30: return 0.5
    else: return max(0.1, 0.5 * (0.95 ** (days_old - 30)))


def filter_adherence_score(job: dict, filters: dict) -> float:
    if not filters:
        return 1.0
    total, matched = 0, 0
    if "remote" in filters and filters["remote"] is not None:
        total += 1
        if job.get("remote") == filters["remote"]:
            matched += 1
    if filters.get("seniority"):
        total += 1
        if job.get("seniority") == filters["seniority"].lower():
            matched += 1
    if filters.get("location"):
        total += 1
        if filters["location"].lower() in job.get("location", "").lower() or job.get("remote"):
            matched += 1
    if filters.get("min_salary"):
        total += 1
        if job.get("salary_min", 0) >= filters["min_salary"]:
            matched += 1
    return matched / total if total > 0 else 1.0


def bonus_score(candidate_skills: list[str], job_skills: list[str]) -> float:
    cv_set = normalize_skills(candidate_skills)
    job_set = normalize_skills(job_skills)
    bonus = sum(v for k, v in HIGH_VALUE_SKILLS.items()
                if k.lower() in cv_set and k.lower() in job_set)
    return min(0.10, bonus)


def calculate_final_score(
    candidate_skills,
    job,
    candidate_seniority="junior",
    filters=None,
    resume_text: str = "",
):
    filters = filters or {}
    job_skills = job.get("skills_required", [])
    s_skills = skill_score(
        candidate_skills,
        job_skills,
        resume_text=resume_text,
        job=job,
    )
    s_seniority = seniority_score(candidate_seniority, job.get("seniority", "any"))
    s_recency   = recency_score(job.get("posted_at", ""))
    s_filters   = filter_adherence_score(job, filters)
    s_bonus     = bonus_score(candidate_skills, job_skills)
    final = (0.40 * s_skills + 0.20 * s_seniority +
             0.15 * s_recency + 0.15 * s_filters + s_bonus)
    cv_set = normalize_skills(candidate_skills)
    job_set_list = job.get("skills_required", [])
    matched = [s for s in job_set_list if s.lower() in cv_set]
    missing = [s for s in job_set_list if s.lower() not in cv_set]
    percent = round(final * 100)
    if percent >= 80:   opener = f"Excelente match ({percent}%)"
    elif percent >= 60: opener = f"Bom match ({percent}%)"
    elif percent >= 40: opener = f"Match parcial ({percent}%)"
    else:               opener = f"Match fraco ({percent}%)"
    parts = [opener]
    if matched: parts.append(f"você tem: {', '.join(matched[:4])}")
    if missing: parts.append(f"faltam: {', '.join(missing[:3])}")
    if not missing: parts.append("você tem todas as skills exigidas")
    try:
        from app.services.hiring_predictor import predict_hiring_probability
        hiring_prob = predict_hiring_probability(
            semantic_score=s_skills,
            candidate_skills=candidate_skills,
            job_skills=job_skills,
            candidate_seniority=candidate_seniority,
            job_seniority=job.get("seniority", "any"),
        )
    except Exception as e:
        print(f"Hiring predictor falhou: {e}")
        hiring_prob = 0.0

    return {
        "score": round(final, 3),
        "score_percent": f"{percent}%",
        "reason": " — ".join(parts) + ".",
        "matched_skills": matched,
        "missing_skills": missing,
        "hiring_probability": hiring_prob,
        "breakdown": {
            "skills": round(s_skills, 3),
            "seniority": round(s_seniority, 3),
            "recency": round(s_recency, 3),
            "filters": round(s_filters, 3),
            "bonus": round(s_bonus, 3),
        },
    }


def rank_jobs(
    jobs,
    candidate_skills,
    candidate_seniority="junior",
    filters=None,
    min_score=0.0,
    limit=20,
    resume_text: str = "",
):
    results = []
    for job in jobs:
        match = calculate_final_score(
            candidate_skills,
            job,
            candidate_seniority,
            filters,
            resume_text=resume_text,
        )
        if match["score"] >= min_score:
            results.append({
                "job": {
                    "id": job.get("id"), "title": job.get("title"),
                    "company": job.get("company"), "location": job.get("location"),
                    "remote": job.get("remote"), "seniority": job.get("seniority"),
                    "salary_min": job.get("salary_min"), "salary_max": job.get("salary_max"),
                    "posted_at": job.get("posted_at"), "url": job.get("url"),
                    "source": job.get("source", "adzuna"), "country": job.get("country", "gb"),
                },
                "score": match["score"],
                "score_percent": match["score_percent"],
                "reason": match["reason"],
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
                "hiring_probability": match["hiring_probability"],
                "breakdown": match["breakdown"],
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def get_top_missing_skills(ranked_results: list[dict], top_n: int = 5) -> list[dict]:
    skill_count: dict[str, int] = {}
    for result in ranked_results[:10]:
        for skill in result.get("missing_skills", []):
            skill_count[skill.lower()] = skill_count.get(skill.lower(), 0) + 1
    sorted_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)
    return [{"skill": s, "appears_in_top_jobs": c} for s, c in sorted_skills[:top_n]]