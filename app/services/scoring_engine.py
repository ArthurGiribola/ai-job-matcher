from collections import Counter
from datetime import datetime, timezone

from app.models.job import Job
from app.models.match import MatchFilters

LEVELS = {
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
    "any": 0,
}

HIGH_VALUE = {
    "AWS": 0.03,
    "GCP": 0.03,
    "Azure": 0.03,
    "Machine Learning": 0.04,
    "Python": 0.02,
    "Kubernetes": 0.03,
    "Terraform": 0.02,
    "System Design": 0.03,
    "LLM": 0.05,
}


def normalize_skills(skills: list[str] | set[str]) -> set[str]:
    return {skill.strip() for skill in skills if skill and skill.strip()}


def skill_score(cv_skills: set[str], job_skills: list[str]) -> float:
    job_set = normalize_skills(job_skills)

    if not cv_skills and not job_set:
        return 1.0

    if not job_set:
        return 0.5

    inter = cv_skills & job_set
    union = cv_skills | job_set
    jaccard = len(inter) / len(union) if union else 0.0

    must_have = set(job_skills[:3])
    bonus = len(cv_skills & must_have) * 0.05

    return min(1.0, jaccard + bonus)


def seniority_score(cv_level: str, job_level: str) -> float:
    cv_value = LEVELS.get(cv_level, 0)
    job_value = LEVELS.get(job_level, 0)

    if cv_value == 0 or job_value == 0:
        return 1.0

    diff = abs(cv_value - job_value)
    return [1.0, 0.7, 0.3, 0.0][min(diff, 3)]


def recency_score(posted_at: datetime) -> float:
    now = datetime.now(timezone.utc)

    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    days_old = (now - posted_at).days

    if days_old <= 3:
        return 1.0
    if days_old <= 7:
        return 0.9
    if days_old <= 14:
        return 0.75
    if days_old <= 30:
        return 0.5

    return max(0.1, 0.5 * (0.95 ** (days_old - 30)))


def filter_adherence(job: Job, filters: MatchFilters) -> float:
    checks: list[bool] = []

    if filters.title:
        checks.append(filters.title.lower() in job.title.lower())

    if filters.location:
        checks.append(filters.location.lower() in job.location.lower())

    if filters.remote is not None:
        checks.append(filters.remote == job.remote)

    if filters.seniority:
        checks.append(filters.seniority == job.seniority)

    if filters.stack:
        checks.append(len(normalize_skills(filters.stack) & normalize_skills(job.skills_required)) > 0)

    if not checks:
        return 1.0

    return sum(checks) / len(checks)


def bonus_score(cv_skills: set[str], job_skills: list[str]) -> float:
    job_set = normalize_skills(job_skills)
    value = sum(
        weight
        for skill, weight in HIGH_VALUE.items()
        if skill in cv_skills and skill in job_set
    )
    return min(0.1, value)


def generate_reason(score: float, cv_skills: set[str], job: Job, gaps: list[str]) -> str:
    highlights = sorted(list(cv_skills & normalize_skills(job.skills_required)))[:4]

    parts = [f"Match de {round(score * 100)}%"]

    if highlights:
        parts.append("você tem " + ", ".join(highlights))

    if gaps:
        parts.append("faltam: " + ", ".join(gaps[:3]))

    return " — ".join(parts) + "."


def final_score(cv_skills, cv_seniority, job, filters):
    # NORMALIZA
    cv_set = set([s.lower() for s in cv_skills])
    job_set = set([s.lower() for s in job.skills_required])

    # MATCH
    matched = cv_set & job_set
    missing = job_set - cv_set

    # SCORE
    score = len(matched) / len(job_set) if job_set else 0
    score = round(score, 3)

    # REASON
    if matched:
        reason = f"Match de {int(score*100)}% — você tem: {', '.join(matched)}"
    else:
        reason = "Nenhuma skill compatível encontrada"

    if missing:
        reason += f" — faltam: {', '.join(missing)}"

    return {
        "score": score,
        "reason": reason,
        "gaps": list(missing),
        "highlight_skills": list(matched)
    }


def aggregate_missing_skills(results):
    skills = []
    for r in results:
        skills.extend(r["gaps"])

    return list(set(skills))