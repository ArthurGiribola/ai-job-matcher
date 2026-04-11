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


def generate_cover_letter_v2(
    analysis: dict,
    job: dict,
    matched_skills: list = None,
    original_letter: str = None,
) -> dict:
    """
    Generates two cover letter versions (Professional + Bold).
    Rewrite mode: scores the original, identifies issues, rewrites both.
    Generate mode: creates both versions from scratch.
    Returns dict: score, key_issues, recruiter_perspective, version_a, version_b, what_improved.
    """
    empty = {
        "score": None, "key_issues": [], "recruiter_perspective": "",
        "version_a": "", "version_b": "", "what_improved": [],
    }
    try:
        client = _get_client()

        if matched_skills:
            top_skills = matched_skills[:3]
        else:
            candidate_set = {s["name"].lower() for s in analysis.get("skills", [])}
            top_skills = [s for s in job.get("skills_required", []) if s.lower() in candidate_set][:3]
        if not top_skills:
            top_skills = [s["name"] for s in analysis.get("skills", [])[:3]]

        strengths = analysis.get("strengths", [])
        concrete_example = strengths[0] if strengths else analysis.get("profile_summary", "")

        if original_letter:
            mode_block = f"""MODE: REWRITE
Analyze this existing cover letter, score it, identify weaknesses, then rewrite it.

ORIGINAL COVER LETTER:
\"\"\"{original_letter}\"\"\"

"""
        else:
            mode_block = "MODE: GENERATE (create from scratch)\n\n"

        prompt = f"""{mode_block}Return ONLY a valid JSON object — no other text, no markdown fences:
{{
  "score": <int 0-100 if REWRITE, null if GENERATE>,
  "key_issues": [<2-4 specific weaknesses if REWRITE, else []>],
  "recruiter_perspective": "<one honest recruiter sentence if REWRITE, else ''>",
  "version_a": "<Professional & Polished, 150-250 words>",
  "version_b": "<Bold & High-Performer, 150-250 words, stronger verbs, more direct>",
  "what_improved": [<2-4 concrete improvements vs original or vs generic letters>]
}}

Candidate:
- Name: {analysis.get('name', 'the candidate')}
- Level: {analysis.get('seniority', 'junior')}
- Experience: {analysis.get('experience_years', 0)} years
- Top skills matching this role: {top_skills}
- Concrete achievement: {concrete_example}
- Profile summary: {analysis.get('profile_summary', '')}

Job:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Required skills: {job.get('skills_required', [])[:6]}
- Level: {job.get('seniority')}

Writing rules (enforce strictly in BOTH versions):
- 150-250 words each — count them
- FORBIDDEN phrases: "excited to apply", "believe my skills align", "passion for", "team player", "I am writing to", "I am pleased to"
- Mention "{job.get('company')}" and "{job.get('title')}" explicitly by name
- Include this concrete example: {concrete_example}
- Human tone — no symmetric sentence pairs, no over-polished language
- Confident, specific call to action at the end
- NO date, address, or formal header
- LANGUAGE: detect from profile_summary — write in Portuguese if PT, English if EN
- Version A: structured, professional, measured
- Version B: direct, bold, high-performer energy — reads like someone who knows their value"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        for key in ("version_a", "version_b"):
            if not result.get(key):
                return empty

        result.setdefault("score", None)
        result.setdefault("key_issues", [])
        result.setdefault("recruiter_perspective", "")
        result.setdefault("what_improved", [])

        chars = len(result["version_a"]) + len(result["version_b"])
        print(f"[Claude OK] generate_cover_letter_v2 — {chars} chars total")
        return result

    except json.JSONDecodeError as e:
        print(f"[Claude FAIL] generate_cover_letter_v2 — JSONDecodeError: {e}")
        return empty
    except Exception as e:
        print(f"[Claude FAIL] generate_cover_letter_v2 — {type(e).__name__}: {e}")
        return empty


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


def suggest_resume_improvements(
    analysis: dict,
    job: dict,
    resume_text: str,
) -> str:
    """
    Analisa o currículo vs a vaga e sugere melhorias específicas.
    Retorna sugestões em português do Brasil.
    """
    try:
        client = _get_client()
        prompt = f"""Você é um coach de carreira especialista em recrutamento técnico.

Analise o currículo abaixo comparado com a vaga e gere sugestões ESPECÍFICAS e ACIONÁVEIS de melhoria.

Perfil extraído do currículo:
- Nível: {analysis.get('seniority')}
- Skills: {[s['name'] for s in analysis.get('skills', [])[:10]]}
- Complexidade dos projetos: {analysis.get('project_complexity')}
- Red flags: {analysis.get('red_flags', [])}
- Resumo: {analysis.get('profile_summary', '')}

Vaga:
- Cargo: {job.get('title')} em {job.get('company')}
- Skills exigidas: {job.get('skills_required', [])[:10]}
- Nível: {job.get('seniority')}
- Skills que o candidato não tem: {job.get('skills_required', [])}

Trecho do currículo:
{resume_text[:2000]}

Gere exatamente 5 sugestões específicas no formato:
1. [SEÇÃO] Sugestão específica e acionável
2. [SEÇÃO] Sugestão específica e acionável
...

Onde SEÇÃO pode ser: EXPERIÊNCIA, PROJETOS, SKILLS, RESUMO, EDUCAÇÃO

Regras:
- Seja específico — não diga "adicione mais detalhes", diga EXATAMENTE o que adicionar
- Base tudo no currículo real — não invente experiências
- Foque nas skills que a vaga pede e o candidato tem mas não destacou
- SEMPRE em português do Brasil
- Máximo 2 linhas por sugestão"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        print(f"[Claude OK] suggest_resume_improvements — {len(result)} chars")
        return result
    except Exception as e:
        print(f"[Claude FAIL] suggest_resume_improvements — {type(e).__name__}: {e}")
        return ""


def validate_resume_quality(resume_text: str) -> dict:
    """
    Valida a qualidade do currículo antes da análise.
    Retorna score de qualidade e lista de problemas encontrados.
    """
    import re

    warnings = []
    score = 100

    # Verifica tamanho
    word_count = len(resume_text.split())
    if word_count < 100:
        warnings.append("⚠️ Currículo muito curto — adicione mais detalhes sobre experiências e projetos")
        score -= 30
    elif word_count < 200:
        warnings.append("⚠️ Currículo curto — considere expandir suas experiências")
        score -= 15

    # Verifica contato
    if not re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]+', resume_text):
        warnings.append("⚠️ Email não encontrado — adicione seu contato")
        score -= 10
    if not re.search(r'linkedin\.com', resume_text, re.I):
        warnings.append("💡 LinkedIn não encontrado — adicione seu perfil")
        score -= 5

    # Verifica seções importantes
    text_lower = resume_text.lower()
    if not any(w in text_lower for w in ['experience', 'experiência', 'trabalho', 'work']):
        warnings.append("⚠️ Seção de experiência não encontrada")
        score -= 20
    if not any(w in text_lower for w in ['project', 'projeto', 'portfolio']):
        warnings.append("⚠️ Seção de projetos não encontrada — projetos são essenciais para tech")
        score -= 15
    if not any(w in text_lower for w in ['education', 'educação', 'university', 'faculdade', 'curso']):
        warnings.append("⚠️ Seção de educação não encontrada")
        score -= 10

    # Verifica skills técnicas
    tech_keywords = ['python', 'java', 'javascript', 'sql', 'git', 'docker', 'aws', 'react', 'node']
    found_tech = [k for k in tech_keywords if k in text_lower]
    if len(found_tech) < 2:
        warnings.append("⚠️ Poucas skills técnicas identificadas — liste suas habilidades claramente")
        score -= 10

    # Verifica métricas
    if not re.search(r'\d+%|\d+ anos|\d+ months|\d+ projetos', resume_text, re.I):
        warnings.append("💡 Adicione métricas aos seus projetos (ex: 'reduziu tempo em 30%', '5 projetos entregues')")
        score -= 5

    quality_label = "🟢 Excelente" if score >= 80 else "🟡 Bom" if score >= 60 else "🔴 Precisa melhorar"

    return {
        "score": max(0, score),
        "label": quality_label,
        "warnings": warnings,
        "word_count": word_count,
    }


def detect_job_red_flags(job: dict) -> list[str]:
    """
    Detecta red flags na descrição da vaga.
    Retorna lista de avisos sem chamar Claude — análise local.
    """
    flags = []
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()
    text = f"{title} {description}"

    # Salário
    if not job.get("salary_min") and not job.get("salary_max"):
        flags.append("💰 Salário não informado — pergunte na entrevista")

    # Exigências excessivas para nível junior
    senior_words = ["5+ years", "10 years", "extensive experience", "expert level"]
    if job.get("seniority") == "junior" and any(w in text for w in senior_words):
        flags.append("⚠️ Vaga junior com exigências de senior — verifique antes de aplicar")

    # Urgência suspeita
    if any(w in text for w in ["urgent", "immediately", "asap", "urgente"]):
        flags.append("⚡ Vaga com urgência — pode indicar alta rotatividade")

    # Empresa sem informação
    if job.get("company", "").lower() in ["company", "confidential", ""]:
        flags.append("🏢 Empresa não identificada — pesquise antes de aplicar")

    # Stack muito ampla
    skills = job.get("skills_required", [])
    if len(skills) > 10:
        flags.append(f"📋 Muitas skills exigidas ({len(skills)}) — pode ser vaga mal definida")

    # Palavras positivas demais
    hype_words = ["rockstar", "ninja", "guru", "unicorn", "superhero"]
    if any(w in text for w in hype_words):
        flags.append("🚩 Linguagem de 'rockstar' — cultura pode ser tóxica")

    return flags


def translate_resume_to_english(resume_text: str, analysis: dict) -> str:
    """
    Traduz e adapta o currículo para inglês profissional.
    """
    try:
        client = _get_client()
        prompt = f"""You are a professional resume translator and career coach.

Translate and adapt this resume to professional English.

Rules:
- Keep all facts exactly as they are — do NOT invent or add anything
- Use professional English resume language
- Convert Brazilian Portuguese terms to English equivalents
- Keep technical terms in English (they already are)
- Format cleanly with sections: Summary, Experience, Projects, Education, Skills
- Use action verbs (Developed, Implemented, Designed, Built)
- Keep it concise and ATS-friendly

Resume to translate:
{resume_text[:3000]}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        print(f"[Claude OK] translate_resume_to_english — {len(result)} chars")
        return result
    except Exception as e:
        print(f"[Claude FAIL] translate_resume_to_english — {type(e).__name__}: {e}")
        return ""


def generate_full_resume(
    analysis: dict,
    resume_text: str,
    job: dict = None,
) -> str:
    """
    Gera um currículo novo completo e profissional baseado no original.
    Se job for fornecido, otimiza para aquela vaga específica.
    """
    try:
        client = _get_client()

        job_context = ""
        if job:
            job_context = f"""
Otimize especificamente para esta vaga:
- Cargo: {job.get('title')} em {job.get('company')}
- Skills exigidas: {job.get('skills_required', [])[:10]}
- Nível: {job.get('seniority')}
"""

        prompt = f"""Você é um especialista em redação de currículos técnicos com 15 anos de experiência em recrutamento de tecnologia.

Gere um currículo NOVO, profissional e completo baseado nas informações abaixo.
{job_context}

Perfil extraído:
- Nível: {analysis.get('seniority')}
- Skills: {[s['name'] for s in analysis.get('skills', [])[:15]]}
- Experiência: {analysis.get('experience_years')} anos
- Pontos fortes: {analysis.get('strengths', [])[:5]}
- Resumo atual: {analysis.get('profile_summary', '')}

Currículo original:
{resume_text[:3000]}

Regras OBRIGATÓRIAS:
- NÃO invente experiências, empresas ou projetos que não existem
- Use APENAS informações do currículo original
- Reescreva com linguagem mais profissional e impactante
- Use verbos de ação fortes (Desenvolvi, Implementei, Otimizei, Construí)
- Adicione métricas onde fizer sentido baseado no contexto
- Formato: Markdown bem estruturado
- Idioma: Português do Brasil
- Inclua TODAS as seções: Resumo Profissional, Experiência, Projetos, Educação, Skills, Idiomas

Estrutura obrigatória:
# [Nome]
**[Título Profissional]**
[Contato]

## Resumo Profissional
[3-4 linhas impactantes]

## Experiência Profissional
[Experiências reescritas com bullets impactantes]

## Projetos
[Projetos com tecnologias e resultados]

## Educação
[Formação]

## Skills Técnicas
[Skills organizadas por categoria]

## Idiomas
[Idiomas]"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        print(f"[Claude OK] generate_full_resume — {len(result)} chars")
        return result
    except Exception as e:
        print(f"[Claude FAIL] generate_full_resume — {type(e).__name__}: {e}")
        return ""
