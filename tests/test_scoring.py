"""
Testes unitários — Scoring Engine
Roda com: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scoring_engine import (
    skill_score,
    seniority_score,
    recency_score,
    calculate_final_score,
    rank_jobs,
    get_top_missing_skills,
    normalize_skills,
)
from app.services.resume_parser import (
    extract_skills,
    detect_seniority,
    clean_text,
)


# ── Skill Score ───────────────────────────────────────────────────────────────

def test_skill_score_perfect_match():
    cv = ["Python", "FastAPI", "Docker"]
    job = ["Python", "FastAPI", "Docker"]
    assert skill_score(cv, job) >= 0.9

def test_skill_score_no_match():
    cv = ["Java", "Spring"]
    job = ["Python", "FastAPI", "Docker"]
    assert skill_score(cv, job) == 0.0

def test_skill_score_partial_match():
    cv = ["Python", "Java"]
    job = ["Python", "FastAPI", "Docker"]
    score = skill_score(cv, job)
    assert 0.0 < score < 1.0

def test_skill_score_empty_job():
    cv = ["Python"]
    job = []
    assert skill_score(cv, job) == 0.5

def test_skill_score_case_insensitive():
    cv = ["python", "FASTAPI"]
    job = ["Python", "FastAPI"]
    assert skill_score(cv, job) >= 0.9


# ── Seniority Score ───────────────────────────────────────────────────────────

def test_seniority_exact_match():
    assert seniority_score("junior", "junior") == 1.0

def test_seniority_one_level_diff():
    assert seniority_score("junior", "mid") == 0.7

def test_seniority_two_levels_diff():
    assert seniority_score("junior", "senior") == 0.3

def test_seniority_any_level():
    assert seniority_score("junior", "any") == 1.0
    assert seniority_score("senior", "any") == 1.0


# ── Recency Score ─────────────────────────────────────────────────────────────

def test_recency_recent_job():
    from datetime import date, timedelta
    today = date.today().strftime("%Y-%m-%d")
    assert recency_score(today) == 1.0

def test_recency_old_job():
    assert recency_score("2025-01-01") <= 0.5

def test_recency_invalid_date():
    assert recency_score("invalid") == 0.5


# ── Final Score ───────────────────────────────────────────────────────────────

def test_final_score_structure():
    cv_skills = ["Python", "FastAPI", "Docker"]
    job = {
        "id": "test_001",
        "title": "Backend Engineer",
        "company": "Test Co",
        "seniority": "junior",
        "skills_required": ["Python", "FastAPI", "Docker"],
        "posted_at": "2026-03-28",
        "remote": True,
        "location": "São Paulo",
        "salary_min": 5000,
        "salary_max": 10000,
    }
    result = calculate_final_score(cv_skills, job, "junior")
    assert "score" in result
    assert "score_percent" in result
    assert "reason" in result
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert "breakdown" in result

def test_final_score_range():
    cv_skills = ["Python"]
    job = {
        "seniority": "junior",
        "skills_required": ["Python", "FastAPI"],
        "posted_at": "2026-03-28",
        "remote": True,
        "location": "Remote",
    }
    result = calculate_final_score(cv_skills, job)
    assert 0.0 <= result["score"] <= 1.0

def test_final_score_perfect():
    skills = ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"]
    job = {
        "seniority": "junior",
        "skills_required": ["Python", "FastAPI", "Docker"],
        "posted_at": "2026-03-29",
        "remote": True,
        "location": "Remote",
    }
    result = calculate_final_score(skills, job, "junior")
    assert result["score"] >= 0.7


# ── Rank Jobs ─────────────────────────────────────────────────────────────────

def test_rank_jobs_returns_sorted():
    jobs = [
        {"id": "1", "seniority": "senior", "skills_required": ["Kubernetes", "Terraform"], "posted_at": "2026-01-01", "remote": True, "location": "Remote"},
        {"id": "2", "seniority": "junior", "skills_required": ["Python", "FastAPI"], "posted_at": "2026-03-28", "remote": True, "location": "Remote"},
    ]
    cv = ["Python", "FastAPI"]
    results = rank_jobs(jobs, cv, "junior")
    assert results[0]["score"] >= results[-1]["score"]

def test_rank_jobs_limit():
    jobs = [
        {"id": str(i), "seniority": "junior", "skills_required": ["Python"], "posted_at": "2026-03-28", "remote": True, "location": "Remote"}
        for i in range(10)
    ]
    results = rank_jobs(jobs, ["Python"], limit=3)
    assert len(results) <= 3


# ── Resume Parser ─────────────────────────────────────────────────────────────

def test_extract_skills_basic():
    text = "Experienced with Python, FastAPI, Docker and AWS"
    skills = extract_skills(text)
    assert "Python" in skills
    assert "Docker" in skills
    assert "AWS" in skills

def test_extract_skills_aliases():
    text = "Built with nodejs and sklearn"
    skills = extract_skills(text)
    assert "Node.js" in skills
    assert "scikit-learn" in skills

def test_detect_seniority_junior():
    text = "Seeking a junior role as an intern"
    assert detect_seniority(text) == "junior"

def test_detect_seniority_senior():
    text = "Senior engineer with 7 anos of experience"
    assert detect_seniority(text) == "senior"

def test_clean_text():
    text = "Hello   World\n\nTest   "
    result = clean_text(text)
    assert "  " not in result
    assert result == result.lower()

def test_normalize_skills():
    skills = ["Python ", "FASTAPI", " docker"]
    result = normalize_skills(skills)
    assert "python" in result
    assert "fastapi" in result
    assert "docker" in result
