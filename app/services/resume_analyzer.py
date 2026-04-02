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


def _get_api_key() -> str | None:
    """Lê ANTHROPIC_API_KEY do .env, st.secrets ou variável de ambiente."""
    # 1. .env local (via python-dotenv)
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    # 2. Streamlit Cloud secrets (dashboard ou .streamlit/secrets.toml)
    try:
        import streamlit as st
        key = st.secrets["ANTHROPIC_API_KEY"]
        if key:
            return key
    except KeyError:
        print("ANTHROPIC_API_KEY not found in st.secrets")
    except Exception as e:
        print(f"Could not read st.secrets: {e}")
    return None


def _get_client():
    """Cria o client Anthropic — lê chave do .env ou st.secrets."""
    import anthropic
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY não encontrada. "
            "Defina via .env (local) ou Streamlit Cloud > Settings > Secrets."
        )
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
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(resume_text=resume_text[:4000])
                }
            ]
        )
        raw = message.content[0].text
        result = _parse_claude_response(raw)
        result["source"] = "claude"
        print(f"[Claude OK] analyze_resume — {len(raw)} chars")
        return result
    except json.JSONDecodeError as e:
        print(f"[Claude FAIL] analyze_resume — {type(e).__name__}: {e}")
        return _fallback_analysis(resume_text)
    except Exception as e:
        print(f"[Claude FAIL] analyze_resume — {type(e).__name__}: {e}")
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


def generate_cover_letter(
    analysis: dict,
    job: dict,
    matched_skills: list = None,
) -> str:
    """
    Gera cover letter personalizado baseado no perfil do candidato e na vaga.
    Detecta o idioma do currículo e escreve no mesmo idioma.
    Máximo 250 palavras. Menciona top 3 skills que coincidem e um projeto concreto.
    """
    try:
        client = _get_client()

        # Top 3 skills que o candidato tem E a vaga pede
        if matched_skills:
            top_skills = matched_skills[:3]
        else:
            candidate_set = {s["name"].lower() for s in analysis.get("skills", [])}
            job_skills = job.get("skills_required", [])
            top_skills = [s for s in job_skills if s.lower() in candidate_set][:3]
        if not top_skills:
            top_skills = [s["name"] for s in analysis.get("skills", [])[:3]]

        # Projeto concreto — usa primeiro ponto forte ou trecho do resumo
        strengths = analysis.get("strengths", [])
        concrete_example = strengths[0] if strengths else analysis.get("profile_summary", "")

        prompt = f"""You are an expert professional writer and recruiter.

Write a cover letter for this job application.

Candidate profile:
- Name: {analysis.get('name', 'the candidate')}
- Level: {analysis.get('seniority', 'junior')}
- Experience: {analysis.get('experience_years', 0)} years
- Top matching skills for this role: {top_skills}
- Concrete example / strength: {concrete_example}
- Profile summary: {analysis.get('profile_summary', '')}

Job:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Required skills: {job.get('skills_required', [])[:6]}
- Level: {job.get('seniority')}

Rules (follow strictly):
- MAXIMUM 250 words — count them
- Exactly 3 short paragraphs
- Mention the job title "{job.get('title')}" and company "{job.get('company')}" by name
- Mention these specific skills: {top_skills}
- Reference this concrete example: {concrete_example}
- End with a clear call to action
- Do NOT invent experience that is not in the profile
- Do NOT include date, address, or formal header
- IMPORTANT: Detect the language of the profile_summary field and write the entire cover letter in THAT SAME LANGUAGE. If summary is in Portuguese, write in Portuguese. If in English, write in English."""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        print(f"[Claude OK] generate_cover_letter — {len(result)} chars")
        return result
    except Exception as e:
        print(f"[Claude FAIL] generate_cover_letter — {type(e).__name__}: {e}")
        return ""


def generate_job_explanation(
    analysis: dict,
    job: dict,
    match_result: dict,
) -> str:
    """
    Gera explicação personalizada de por que o candidato
    deve ou não se candidatar a essa vaga.
    Chamada apenas para as top 3 vagas.
    """
    try:
        client = _get_client()
        prompt = f"""You are a brutally honest career coach.

Candidate profile:
- Seniority: {analysis.get('seniority')}
- Experience: {analysis.get('experience_years')} years
- Skills: {[s['name'] for s in analysis.get('skills', [])[:10]]}
- Project complexity: {analysis.get('project_complexity')}
- Red flags: {analysis.get('red_flags', [])}

Job: {job.get('title')} at {job.get('company')}
- Required skills: {job.get('skills_required', [])}
- Seniority: {job.get('seniority')}
- Match score: {match_result.get('score_percent')}
- Missing skills: {match_result.get('missing_skills', [])}

In 2-3 sentences in Portuguese, explain:
1. The main reason to apply or not apply
2. What to emphasize in the application
3. The biggest gap to address

IMPORTANTE: Responda SEMPRE em português do Brasil, independente do idioma do currículo ou da vaga.
Be direct and actionable. No fluff."""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        print(f"[Claude OK] generate_job_explanation — {len(result)} chars")
        return result
    except Exception as e:
        print(f"[Claude FAIL] generate_job_explanation — {type(e).__name__}: {e}")
        return ""
