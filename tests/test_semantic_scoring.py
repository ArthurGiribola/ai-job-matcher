import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scoring_engine import rank_jobs

resume = "Python developer with Machine Learning experience. Skills: Python, scikit-learn, pandas, AWS, Git."

jobs = [
    {
        "id": "1",
        "title": "ML Engineer",
        "company": "Test",
        "seniority": "junior",
        "skills_required": ["Python", "scikit-learn", "Machine Learning"],
        "posted_at": "2026-04-01",
        "remote": True,
        "location": "Remote",
        "salary_min": 5000,
        "salary_max": 10000,
        "description": "Build ML models with Python and scikit-learn.",
        "source": "test",
    },
    {
        "id": "2",
        "title": "Frontend Developer",
        "company": "Test",
        "seniority": "junior",
        "skills_required": ["React", "TypeScript", "CSS"],
        "posted_at": "2026-04-01",
        "remote": True,
        "location": "Remote",
        "salary_min": 5000,
        "salary_max": 10000,
        "description": "Build web interfaces with React and TypeScript.",
        "source": "test",
    },
]

results = rank_jobs(
    jobs=jobs,
    candidate_skills=["Python", "scikit-learn", "pandas"],
    resume_text=resume,
)

print("Resultado com embedding semântico:\n")
for r in results:
    print(f"{r['job']['title']} — {r['score_percent']}")
    print(f"  breakdown: {r['breakdown']}")
    print()
