import os
import json
from dotenv import load_dotenv

load_dotenv()

EXTRACTION_PROMPT = """You are an expert technical recruiter with 20 years of experience.
Analyze this resume and extract structured information.

Return ONLY a valid JSON object with this exact structure:
{{
  "skills": [
    {{
      "name": "Python",
      "level": "advanced",
      "years": 2,
      "evidence": "Used in 4 projects including KNN and neural networks"
    }}
  ],
  "seniority": "junior",
  "seniority_reasoning": "7th semester student with academic projects only, no production experience",
  "experience_years": 1,
  "project_complexity": "low",
  "project_complexity_reasoning": "All projects are academic datasets (Titanic, Wine) with no real-world impact",
  "strengths": ["Python fundamentals", "ML algorithms knowledge", "AWS exposure"],
  "weaknesses": ["No production experience", "Only academic projects", "No system design"],
  "profile_summary": "CS student with solid ML foundations but limited real-world exposure",
  "red_flags": ["No deployed systems", "All projects are tutorial-level datasets"]
}}

Rules:
- level must be one of: beginner, intermediate, advanced, expert
- seniority must be one of: intern, junior, mid, senior, lead
- project_complexity must be one of: low, medium, high
- Be brutally honest - do not overestimate
- Base everything on evidence from the resume
- Return ONLY the JSON, no other text

Resume:
{resume_text}"""

def _get_client():
    """Cria o client Anthropic sob demanda — evita erro na importação."""
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não encontrada no .env")
    return anthropic.Anthropic(api_key=api_key)


def _parse_claude_response(raw: str) -> dict:
    """Extrai JSON da resposta do Claude."""
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


def analyze_resume(resume_text: str) -> dict:
    try:
        client = _get_client()

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(resume_text=resume_text[:4000])
                }
            ]
        )

        raw = message.content[0].text
        print(f"DEBUG RAW: {repr(raw[:200])}")
        result = _parse_claude_response(raw)
        result["source"] = "claude"
        return result

    except json.JSONDecodeError as e:
        print(f"Erro JSON: {e}")
        return _fallback_analysis(resume_text)
    except Exception as e:
        print(f"Erro Claude: {e}")
        return _fallback_analysis(resume_text)


def _fallback_analysis(resume_text: str) -> dict:
    from app.services.resume_parser import parse_resume_text
    basic = parse_resume_text(resume_text)
    return {
        "skills": [{"name": s, "level": "unknown", "years": 0, "evidence": ""} for s in basic["skills"]],
        "seniority": basic["seniority"],
        "seniority_reasoning": "Detected by keyword matching (fallback)",
        "experience_years": 0,
        "project_complexity": "low",
        "project_complexity_reasoning": "Could not analyze with LLM",
        "strengths": basic.get("strengths", []),
        "weaknesses": [],
        "profile_summary": "Analysis unavailable",
        "red_flags": [],
        "source": "fallback",
    }


def get_skill_names(analysis: dict) -> list[str]:
    return [s["name"] for s in analysis.get("skills", [])]


def get_skill_levels(analysis: dict) -> dict[str, str]:
    return {s["name"]: s["level"] for s in analysis.get("skills", [])}
