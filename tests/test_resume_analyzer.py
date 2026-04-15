import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.resume_analyzer import analyze_resume, generate_cover_letter_v2, generate_job_explanation

RESUME = """
Arthur Giribola - Computer Science Student 7th semester
Focus on AI Engineering. Seeking internship or junior role.

Skills: Python, C++, Java, pandas, NumPy, scikit-learn,
Machine Learning, Neural Networks, AWS, Git, SQL, Statistics

Projects:
- Wine Classification with KNN
- Titanic Predictive Analysis with Decision Tree
- Artificial Neural Networks with MLP
- Graph Algorithms with Dijkstra in C++

Experience:
- Digital Projects Assistant at Netherix Studios (2023-present)
- Digital Projects Support at Keystone (2021-2023)

Education: B.Sc Computer Science - UNIFAJ (7th semester)
"""

# ── generate_cover_letter_v2 tests ──────────────────────────────────────────

def test_cover_letter_v2_returns_dict():
    """v2 always returns a dict with the required keys."""
    analysis = {"seniority": "junior", "experience_years": 1, "skills": [], "strengths": [], "profile_summary": "test"}
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python"], "seniority": "junior"}
    result = generate_cover_letter_v2(analysis, job)
    assert isinstance(result, dict)
    for key in ("score", "key_issues", "recruiter_perspective", "version_a", "version_b", "what_improved"):
        assert key in result, f"Missing key: {key}"


def test_cover_letter_v2_with_matched_skills():
    """matched_skills param is accepted without error."""
    analysis = {
        "seniority": "junior", "experience_years": 1,
        "skills": [{"name": "Python"}, {"name": "Docker"}],
        "strengths": ["Built a KNN classifier"], "profile_summary": "CS student",
    }
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python", "Docker"], "seniority": "junior"}
    result = generate_cover_letter_v2(analysis, job, matched_skills=["Python", "Docker"])
    assert isinstance(result, dict)
    assert isinstance(result["key_issues"], list)
    assert isinstance(result["what_improved"], list)


def test_cover_letter_v2_rewrite_mode():
    """Rewrite mode (original_letter provided) returns dict without raising."""
    analysis = {"seniority": "junior", "experience_years": 1, "skills": [], "strengths": [], "profile_summary": "test"}
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python"], "seniority": "junior"}
    result = generate_cover_letter_v2(analysis, job, original_letter="I am excited to apply for this role.")
    assert isinstance(result, dict)
    # score should be int or None (not raise)
    assert result["score"] is None or isinstance(result["score"], int)


def test_cover_letter_v2_no_api_returns_empty_dict():
    """Without API key v2 should return the empty dict, not raise."""
    import os
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        analysis = {"seniority": "junior", "experience_years": 0, "skills": [], "strengths": [], "profile_summary": ""}
        job = {"title": "Dev", "company": "Co", "skills_required": [], "seniority": "junior"}
        result = generate_cover_letter_v2(analysis, job)
        assert isinstance(result, dict)
        assert result["version_a"] == ""
        assert result["version_b"] == ""
    finally:
        if original:
            os.environ["ANTHROPIC_API_KEY"] = original


def test_generate_job_explanation_returns_string():
    analysis = {"seniority": "junior", "experience_years": 1, "skills": [], "red_flags": []}
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python"], "seniority": "junior"}
    match_result = {"score_percent": "65%", "missing_skills": []}
    result = generate_job_explanation(analysis, job, match_result)
    assert isinstance(result, str)


def test_analyze_resume_real_api():
    """Teste de integração — chama Claude de verdade. Requer ANTHROPIC_API_KEY."""
    result = analyze_resume(RESUME)
    assert result is not None
    assert "skills" in result
    assert "seniority" in result
    assert result["seniority"] in ("intern", "junior", "mid", "senior", "lead")
