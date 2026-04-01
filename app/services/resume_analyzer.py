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


def generate_cover_letter(
    analysis: dict,
    job: dict,
) -> str:
    """
    Gera cover letter personalizado em português
    baseado no perfil do candidato e na vaga.
    """
    try:
        client = _get_client()
        prompt = f"""Você é um especialista em recrutamento e redação profissional.

Gere um cover letter profissional em português para esta candidatura.

Perfil do candidato:
- Nome: {analysis.get('name', 'Candidato')}
- Nível: {analysis.get('seniority', 'junior')}
- Experiência: {analysis.get('experience_years', 0)} anos
- Skills principais: {[s['name'] for s in analysis.get('skills', [])[:8]]}
- Pontos fortes: {analysis.get('strengths', [])[:3]}
- Resumo: {analysis.get('profile_summary', '')}

Vaga:
- Cargo: {job.get('title')}
- Empresa: {job.get('company')}
- Skills exigidas: {job.get('skills_required', [])[:8]}
- Nível: {job.get('seniority')}

Regras:
- Máximo 3 parágrafos curtos
- Tom profissional mas humano
- Menciona skills que o candidato TEM e a vaga PEDE
- Não inventa experiências que não existem
- Termina com call to action
- Escreve em português do Brasil
- NÃO inclui data, endereço ou cabeçalho formal"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"Cover letter failed: {e}")
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

Be direct and actionable. No fluff."""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"Explanation failed: {e}")
        return ""
