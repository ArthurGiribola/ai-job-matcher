import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.resume_analyzer import analyze_resume

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
