import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.resume_analyzer import analyze_resume, generate_cover_letter, generate_job_explanation

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

def test_generate_cover_letter_returns_string():
    analysis = {"seniority": "junior", "experience_years": 1, "skills": [], "strengths": [], "profile_summary": "test"}
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python"], "seniority": "junior"}
    result = generate_cover_letter(analysis, job)
    assert isinstance(result, str)


def test_generate_job_explanation_returns_string():
    analysis = {"seniority": "junior", "experience_years": 1, "skills": [], "red_flags": []}
    job = {"title": "Python Dev", "company": "Test Co", "skills_required": ["Python"], "seniority": "junior"}
    match_result = {"score_percent": "65%", "missing_skills": []}
    result = generate_job_explanation(analysis, job, match_result)
    assert isinstance(result, str)


print("Analisando curriculo com Claude...\n")
result = analyze_resume(RESUME)

print(f"Source: {result.get('source')}")
print(f"Senioridade: {result['seniority']}")
print(f"Motivo: {result['seniority_reasoning']}")
print(f"Anos de experiencia: {result['experience_years']}")
print(f"Complexidade: {result['project_complexity']}")
print(f"Pontos fortes: {result['strengths']}")
print(f"Pontos fracos: {result['weaknesses']}")
print(f"Red flags: {result['red_flags']}")
print(f"Resumo: {result['profile_summary']}")
print(f"\nSkills:")
for skill in result['skills'][:5]:
    print(f"  {skill['name']} - {skill['level']} - {skill['years']} anos")
