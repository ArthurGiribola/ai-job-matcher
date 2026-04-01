"""
Phase 3 — Hiring Probability Predictor
Logistic Regression treinado em dados sintéticos gerados internamente.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression

SENIORITY_LEVELS = {"junior": 1, "mid": 2, "senior": 3, "lead": 4, "any": 2}

# (semantic, skill_coverage, seniority_gap, exp_gap, has_must, hired)
SYNTHETIC_DATA = [
    (0.90, 0.95,  0,  0,  True,  1),
    (0.85, 0.80,  0, -1,  True,  1),
    (0.75, 0.70,  0,  0,  True,  1),
    (0.70, 0.60,  1, -1,  False, 1),
    (0.65, 0.50,  0,  0,  False, 0),
    (0.50, 0.40, -1, -2,  False, 0),
    (0.40, 0.30, -2, -3,  False, 0),
    (0.80, 0.85, -1,  0,  True,  1),
    (0.60, 0.55,  1,  1,  False, 0),
    (0.95, 1.00,  0,  1,  True,  1),
    (0.30, 0.20, -2, -4,  False, 0),
    (0.72, 0.65,  0, -1,  True,  1),
    (0.55, 0.45, -1, -1,  False, 0),
    (0.88, 0.90,  1,  0,  True,  1),
    (0.45, 0.35, -2, -2,  False, 0),
    (0.78, 0.75,  0,  0,  True,  1),
    (0.62, 0.58,  1, -1,  False, 0),
    (0.92, 0.88,  0,  1,  True,  1),
    (0.35, 0.25, -3, -3,  False, 0),
    (0.68, 0.62,  0,  0,  False, 1),
]


def _build_model() -> LogisticRegression:
    X = np.array([
        [sem, cov, gap, exp, int(must)]
        for sem, cov, gap, exp, must, _ in SYNTHETIC_DATA
    ])
    y = np.array([label for *_, label in SYNTHETIC_DATA])
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    return model


_MODEL = _build_model()


def predict_hiring_probability(
    semantic_score: float,
    candidate_skills: list,
    job_skills: list,
    candidate_seniority: str,
    job_seniority: str,
    candidate_exp_years: int = 0,
) -> float:
    """Retorna probabilidade de chamada para entrevista de 0.0 a 1.0."""
    candidate_set = {s.lower() for s in candidate_skills}
    job_set_lower = [s.lower() for s in job_skills]

    skill_coverage = (
        len([s for s in job_set_lower if s in candidate_set]) / len(job_set_lower)
        if job_set_lower else 0.0
    )

    cand_level = SENIORITY_LEVELS.get(candidate_seniority.lower(), 2)
    job_level = SENIORITY_LEVELS.get(job_seniority.lower(), 2)
    seniority_gap = max(-2, min(2, cand_level - job_level))

    must_have = [s.lower() for s in job_skills[:3]]
    has_all_must = all(s in candidate_set for s in must_have) if must_have else True

    features = np.array([[
        semantic_score,
        skill_coverage,
        seniority_gap,
        float(candidate_exp_years),
        float(has_all_must),
    ]])

    prob = _MODEL.predict_proba(features)[0][1]
    return round(float(prob), 3)
