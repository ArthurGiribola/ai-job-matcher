"""
Teste isolado do embedder.
Roda com: python tests/test_embedder.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedder import resume_job_similarity

RESUME = """
Computer Science student focused on AI and data-driven solutions.
Skills: Python, scikit-learn, pandas, NumPy, Machine Learning,
Neural Networks, AWS, Git, SQL, Statistics.
Projects: KNN wine classification, Titanic decision tree,
MLP neural network, Dijkstra graph algorithm.
"""

JOBS = [
    {
        "title": "Junior Machine Learning Engineer",
        "description": "Build and deploy ML models for recommendation systems. Python required.",
        "skills_required": ["Python", "scikit-learn", "Machine Learning", "pandas", "SQL"],
    },
    {
        "title": "Senior DevOps Engineer",
        "description": "Manage Kubernetes clusters, CI/CD pipelines, Terraform infrastructure.",
        "skills_required": ["Kubernetes", "Terraform", "Docker", "AWS", "CI/CD"],
    },
    {
        "title": "Frontend React Developer",
        "description": "Build responsive web interfaces with React and TypeScript.",
        "skills_required": ["React", "TypeScript", "JavaScript", "CSS", "HTML"],
    },
]

print("Carregando modelo e calculando similaridades...\n")

for job in JOBS:
    score = resume_job_similarity(RESUME, job)
    print(f"Vaga: {job['title']}")
    print(f"Score semântico: {score:.4f} ({round(score * 100)}%)")
    print()
