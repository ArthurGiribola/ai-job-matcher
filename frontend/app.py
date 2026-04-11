import streamlit as st
import tempfile
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_parser import extract_text_from_pdf
from app.services.resume_analyzer import (
    analyze_resume, get_skill_names, generate_job_explanation,
    generate_cover_letter, generate_cover_letter_v2, suggest_resume_improvements,
    validate_resume_quality, detect_job_red_flags, translate_resume_to_english,
    generate_full_resume, calculate_market_score,
)
from app.services.job_collector import get_jobs, SUPPORTED_COUNTRIES
from app.services.database import save_application, load_applications, get_or_create_session_id

@st.cache_data(ttl=1800, show_spinner=False)
def cached_get_jobs(skills_tuple, limit, country_code, city):
    """Wrapper cacheado para get_jobs — evita rebuscar a cada interação."""
    return get_jobs(
        candidate_skills=list(skills_tuple),
        limit=limit,
        country=country_code,
        location=city,
    )
from app.services.scoring_engine import rank_jobs, get_top_missing_skills
from app.services.embedder import warmup_mock_jobs

warmup_mock_jobs()

SKILL_RESOURCES = {
    "Docker": "https://docs.docker.com/get-started/",
    "Kubernetes": "https://kubernetes.io/docs/tutorials/",
    "Aws": "https://aws.amazon.com/training/",
    "Gcp": "https://cloud.google.com/learn",
    "Azure": "https://learn.microsoft.com/en-us/azure/",
    "Llm": "https://www.deeplearning.ai/short-courses/",
    "Tensorflow": "https://www.tensorflow.org/learn",
    "Pytorch": "https://pytorch.org/tutorials/",
    "Machine Learning": "https://www.coursera.org/learn/machine-learning",
    "Python": "https://docs.python.org/3/tutorial/",
    "Fastapi": "https://fastapi.tiangolo.com/tutorial/",
    "Postgresql": "https://www.postgresql.org/docs/current/tutorial.html",
    "Nlp": "https://huggingface.co/learn/nlp-course/",
    "Mlflow": "https://mlflow.org/docs/latest/tutorials-and-examples/",
    "Huggingface": "https://huggingface.co/learn",
    "Power Bi": "https://learn.microsoft.com/en-us/power-bi/",
    "Terraform": "https://developer.hashicorp.com/terraform/tutorials",
    "Langchain": "https://python.langchain.com/docs/get_started/",
    "React": "https://react.dev/learn",
    "Git": "https://git-scm.com/book/en/v2",
    "Sql": "https://www.w3schools.com/sql/",
    "Scikit-Learn": "https://scikit-learn.org/stable/tutorial/",
    "Pandas": "https://pandas.pydata.org/docs/getting_started/",
    "Numpy": "https://numpy.org/learn/",
    "Rest Api": "https://restfulapi.net/",
    "Microservices": "https://microservices.io/",
    "Statistics": "https://www.khanacademy.org/math/statistics-probability",
    "Spark": "https://spark.apache.org/docs/latest/quick-start.html",
    "Airflow": "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/",
    "Graphql": "https://graphql.org/learn/",
    "Linux": "https://linuxjourney.com/",
    "Ci/Cd": "https://www.redhat.com/en/topics/devops/what-is-ci-cd",
    "Mysql": "https://dev.mysql.com/doc/",
    "Typescript": "https://www.typescriptlang.org/docs/",
    "Vue": "https://vuejs.org/guide/introduction.html",
    "Postgresql": "https://www.postgresql.org/docs/current/tutorial.html",
    "Mongodb": "https://www.mongodb.com/docs/manual/tutorial/",
    "Redis": "https://redis.io/docs/getting-started/",
    "C++": "https://www.learncpp.com/",
    "C": "https://www.learn-c.org/",
    "Oop": "https://realpython.com/python3-object-oriented-programming/",
    "Power Bi": "https://learn.microsoft.com/en-us/power-bi/",
    "Tableau": "https://www.tableau.com/learn/training",
    "Angular": "https://angular.io/tutorial",
    "Node.Js": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",
    "Django": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
    "Flask": "https://flask.palletsprojects.com/en/latest/tutorial/",
}

CURRENCY_BY_COUNTRY = {
    "gb": "£", "us": "$", "au": "A$", "ca": "C$",
    "de": "€", "fr": "€", "nl": "€", "at": "€",
    "be": "€", "it": "€", "es": "€", "pl": "€",
    "ch": "CHF", "sg": "S$", "nz": "NZ$",
    "za": "R", "in": "₹", "br": "R$",
    "mx": "$MX", "ru": "₽",
}

COUNTRY_OPTIONS = {name: code for code, name in SUPPORTED_COUNTRIES.items()}


def format_salary(salary_min, salary_max, country_code, source):
    if source in ["gupy", "mock", "linkedin"] or country_code == "br":
        currency = "R$"
    elif source == "remotive":
        currency = "$"
    else:
        currency = CURRENCY_BY_COUNTRY.get(country_code, "£")
    if not salary_min and not salary_max:
        return "Não informado"
    if salary_max:
        return f"{currency} {salary_min:,.0f} – {salary_max:,.0f}"
    return f"{currency} {salary_min:,.0f}+"


if "applied_jobs" not in st.session_state:
    st.session_state.applied_jobs = load_applications()
if "compare_jobs" not in st.session_state:
    st.session_state.compare_jobs = []

st.set_page_config(page_title="AI Job Matcher", page_icon="🎯", layout="wide")

st.title("🎯 AI Job Matcher")
st.markdown("Envie seu currículo e descubra as vagas mais compatíveis com seu perfil — em qualquer lugar do mundo.")

with st.sidebar:
    st.header("⚙️ Filtros")
    seniority = st.selectbox("Nível", ["junior", "mid", "senior", "lead"])
    country_name = st.selectbox("País", list(COUNTRY_OPTIONS.keys()))
    country_code = COUNTRY_OPTIONS[country_name]
    city = st.text_input("Cidade (opcional)", placeholder="Ex: London, Berlin, São Paulo...")
    st.caption("Digite qualquer cidade do mundo")
    remote_only = st.checkbox("Apenas vagas remotas", value=False)
    min_score = st.slider("Score mínimo (%)", 0, 100, 40) / 100
    limit = st.slider("Número de vagas", 5, 20, 10)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Vagas que apliquei")
    if st.session_state.get("applied_jobs"):
        for app_job in st.session_state.applied_jobs:
            title = app_job.get("job_title") or app_job.get("title", "")
            st.sidebar.markdown(
                f"**{title}**  \n"
                f"{app_job['company']} | {app_job['score']} match  \n"
                f"🎯 {app_job['hiring_prob']} prob. | {app_job['applied_at']}"
            )
        if st.sidebar.button("🗑️ Limpar histórico"):
            st.session_state.applied_jobs = []
            st.rerun()
    else:
        st.sidebar.caption("Nenhuma aplicação ainda.")

st.markdown("---")

tab1, tab2 = st.tabs(["📄 Colar texto", "📎 Upload PDF"])
resume_text = ""
resume_text_from_pdf = ""

with tab1:
    resume_text = st.text_area(
        "Cole o texto do seu currículo aqui:",
        height=200,
        placeholder="Cole aqui o conteúdo do seu currículo em texto..."
    )

with tab2:
    uploaded_file = st.file_uploader("Envie seu currículo em PDF", type=["pdf"])
    if uploaded_file is not None:
        with st.spinner("Extraindo texto do PDF..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                resume_text_from_pdf = extract_text_from_pdf(tmp_path)
                os.unlink(tmp_path)
                if resume_text_from_pdf:
                    lines = [l.strip() for l in resume_text_from_pdf.split('\n') if l.strip()]
                    nome = lines[0] if lines else "Candidato"

                    from app.services.resume_parser import parse_resume_text
                    quick_profile = parse_resume_text(resume_text_from_pdf)

                    st.success(f"✅ PDF processado com sucesso!")

                    st.markdown(f"""
                    <div style="background: #1e1e2e; border: 1px solid #444; border-radius: 12px; padding: 20px; margin: 10px 0;">
                        <h3 style="margin:0; color:#fff;">👤 {nome}</h3>
                        <p style="color:#aaa; margin: 4px 0;">{lines[1] if len(lines) > 1 else ''}</p>
                        <p style="color:#888; font-size:0.85em;">{lines[2] if len(lines) > 2 else ''}</p>
                        <hr style="border-color:#333; margin: 12px 0;">
                        <p style="color:#ccc; margin-bottom: 8px;">🛠️ <b>Skills detectadas:</b></p>
                        <p>{' '.join([f'<span style="background:#2d2d4e; color:#7c7cff; padding:3px 10px; border-radius:20px; margin:3px; display:inline-block; font-size:0.85em;">{s}</span>' for s in quick_profile.get("skills", [])[:12]])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Não foi possível extrair texto deste PDF.")
            except Exception as e:
                st.error(f"Erro ao processar PDF: {str(e)}")

final_text = resume_text_from_pdf if resume_text_from_pdf else resume_text

st.markdown("---")
analyze_btn = st.button("🔍 Analisar e Buscar Vagas", type="primary")

if analyze_btn:
    if not final_text or len(final_text) < 50:
        st.error("Por favor, cole o texto ou envie o PDF do seu currículo.")
    else:
        try:
            import time
            progress_placeholder = st.empty()

            def update_progress(msg: str, icon: str = "🔄"):
                progress_placeholder.info(f"{icon} {msg}")

            update_progress("Lendo seu currículo...", "🔍")
            time.sleep(0.5)

            # Valida qualidade do currículo
            quality = validate_resume_quality(final_text)
            if quality["warnings"]:
                with st.expander(f"📋 Qualidade do currículo: {quality['label']} ({quality['score']}/100)", expanded=quality["score"] < 60):
                    st.progress(quality["score"] / 100)
                    for w in quality["warnings"]:
                        st.markdown(w)
                    st.caption(f"📝 {quality['word_count']} palavras no currículo")

            update_progress("Claude está analisando seu perfil...", "🤖")

            analysis = analyze_resume(final_text)
            profile = {
                "skills": get_skill_names(analysis),
                "total_skills": len(analysis.get("skills", [])),
                "seniority": analysis.get("seniority", "junior"),
                "strengths": analysis.get("strengths", []),
                "source": analysis.get("source", "fallback"),
            }

            update_progress("Buscando vagas compatíveis no mundo...", "🌍")
            jobs = cached_get_jobs(
                skills_tuple=tuple(profile["skills"]),
                limit=40,
                country_code=country_code,
                city=city.strip() if city else "",
            )

            update_progress("Calculando compatibilidade semântica...", "📊")
            results = rank_jobs(
                jobs=jobs,
                candidate_skills=profile["skills"],
                candidate_seniority=profile.get("seniority", seniority),
                limit=50,
                resume_text=final_text,
            )
            missing = get_top_missing_skills(results)
            progress_placeholder.empty()

            if remote_only:
                results = [r for r in results if r["job"].get("remote")]
            results_filtered = [r for r in results if r["score"] >= min_score]
            total_qualified = len(results_filtered)
            results = results_filtered[:limit]

            # Persist to session_state so display survives reruns
            st.session_state["last_results"] = results
            st.session_state["last_analysis"] = analysis
            st.session_state["last_profile"] = profile
            st.session_state["last_missing"] = missing
            st.session_state["last_total_qualified"] = total_qualified
            st.session_state["last_country_name"] = country_name
            st.session_state["last_jobs_count"] = len(jobs)

            # Clear per-job cached data from previous search
            for k in [k for k in st.session_state if k.startswith(("cover_data_", "cover_original_", "cover_text_", "explanation_"))]:
                del st.session_state[k]

            st.success(f"✅ {profile['total_skills']} skills encontradas. Análise via {'Claude AI' if analysis.get('source') == 'claude' else 'parser básico'}.")

        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
            st.exception(e)

# ── Display section — runs on every rerun while results exist in session_state ──
if "last_results" in st.session_state:
    results           = st.session_state["last_results"]
    analysis          = st.session_state["last_analysis"]
    profile           = st.session_state["last_profile"]
    missing           = st.session_state["last_missing"]
    total_qualified   = st.session_state["last_total_qualified"]
    country_name_disp = st.session_state.get("last_country_name", country_name)
    jobs_count        = st.session_state["last_jobs_count"]

    # ── Section 1: Perfil ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("👤 Seu Perfil")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Skills encontradas", profile["total_skills"])
    with col2:
        st.metric("Nível detectado", profile["seniority"].upper())
    with col3:
        st.metric("Vagas analisadas", jobs_count)
    with col4:
        st.metric("Matches encontrados", len(results))

    st.markdown("**🛠️ Skills identificadas:**")
    st.markdown("  ".join([f"`{s}`" for s in profile["skills"]]))
    if profile.get("strengths"):
        st.markdown("**⭐ Pontos fortes:** " + "  ".join([f"`{s}`" for s in profile["strengths"][:5]]))

    st.markdown("---")
    col_trans1, col_trans2 = st.columns([3, 1])
    with col_trans1:
        st.markdown("**🌍 Quer candidatar para vagas internacionais?**")
        st.caption("Claude traduz e adapta seu currículo para inglês profissional")
    with col_trans2:
        if st.button("🌍 Traduzir para inglês", key="translate_btn"):
            with st.spinner("🌍 Claude traduzindo seu currículo..."):
                translated = translate_resume_to_english(final_text, analysis)
            if translated:
                st.session_state["translated_resume"] = translated

    if "translated_resume" in st.session_state:
        st.markdown("**🌍 Currículo em inglês:**")
        st.text_area(
            label="",
            value=st.session_state["translated_resume"],
            height=400,
            key="translated_display",
        )
        st.caption("📋 Copie e use para candidaturas internacionais!")
        if st.button("🗑️ Fechar tradução"):
            del st.session_state["translated_resume"]
            st.rerun()

    st.markdown("---")
    st.markdown("**🚀 Quer um currículo novo e profissional?**")
    st.caption("Claude reescreve seu currículo completo com linguagem profissional e impactante")

    col_gen1, col_gen2 = st.columns(2)
    with col_gen1:
        if st.button("✨ Gerar currículo profissional", key="gen_resume_btn"):
            with st.spinner("✨ Claude criando seu novo currículo..."):
                new_resume = generate_full_resume(analysis, final_text)
            if new_resume:
                st.session_state["generated_resume"] = new_resume
                st.session_state["generated_resume_job"] = None

    if "generated_resume" in st.session_state:
        st.markdown("---")
        job_label = st.session_state.get("generated_resume_job")
        title = f"✨ Seu novo currículo profissional{f' — otimizado para: {job_label}' if job_label else ''}:"
        st.markdown(f"**{title}**")
        st.markdown(st.session_state["generated_resume"])
        st.markdown("---")
        st.text_area(
            "📋 Versão para copiar:",
            value=st.session_state["generated_resume"],
            height=400,
            key="generated_resume_copy",
        )
        st.caption("💡 Copie o texto acima e cole no seu editor favorito (Word, Google Docs, Notion)")
        if st.button("🗑️ Fechar currículo gerado", key="close_gen_resume"):
            del st.session_state["generated_resume"]
            st.rerun()

    st.markdown("---")
    st.markdown("**💰 Quanto você vale no mercado?**")
    st.caption("Claude analisa suas skills e calcula sua faixa salarial atual — e como aumentar")

    if st.button("💰 Calcular meu valor de mercado", key="market_score_btn"):
        with st.spinner("💰 Claude analisando o mercado..."):
            market = calculate_market_score(analysis, final_text)
        if market:
            st.session_state["market_score"] = market

    if "market_score" in st.session_state:
        market = st.session_state["market_score"]

        st.markdown("---")
        st.subheader("💰 Seu valor de mercado atual")

        st.info(f"💡 {market.get('insight', '')}")

        col1, col2, col3 = st.columns(3)
        br = market.get("brazil", {})
        uk = market.get("uk", {})
        usa = market.get("usa", {})
        with col1:
            st.markdown("### 🇧🇷 Brasil")
            st.markdown(f"**{br.get('currency', 'R$')} {br.get('min', 0):,.0f} – {br.get('max', 0):,.0f}/{br.get('period', 'mês')}**")
        with col2:
            st.markdown("### 🇬🇧 Reino Unido")
            st.markdown(f"**{uk.get('currency', '£')} {uk.get('min', 0):,.0f} – {uk.get('max', 0):,.0f}/{uk.get('period', 'ano')}**")
        with col3:
            st.markdown("### 🇺🇸 Estados Unidos")
            st.markdown(f"**{usa.get('currency', '$')} {usa.get('min', 0):,.0f} – {usa.get('max', 0):,.0f}/{usa.get('period', 'ano')}**")

        skills_boost = market.get("skills_to_increase_salary", [])
        if skills_boost:
            st.markdown("---")
            st.subheader("📈 Como aumentar seu valor")

            after = market.get("salary_after_skills", {})
            after_br = after.get("brazil", {})
            after_uk = after.get("uk", {})
            after_usa = after.get("usa", {})

            st.markdown("Aprendendo as skills abaixo, você poderia chegar a:")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"🇧🇷 **R$ {after_br.get('min', 0):,.0f} – {after_br.get('max', 0):,.0f}/mês**")
            with col2:
                st.markdown(f"🇬🇧 **£ {after_uk.get('min', 0):,.0f} – {after_uk.get('max', 0):,.0f}/ano**")
            with col3:
                st.markdown(f"🇺🇸 **$ {after_usa.get('min', 0):,.0f} – {after_usa.get('max', 0):,.0f}/ano**")

            st.markdown("**Skills que mais aumentam seu salário:**")
            for skill in skills_boost:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{skill.get('skill')}** — {skill.get('reason')}")
                with col2:
                    st.markdown(f"**{skill.get('impact')}** 💰")

        if st.button("🗑️ Fechar score de mercado", key="close_market"):
            del st.session_state["market_score"]
            st.rerun()

    # ── Section 2: Análise do Claude ────────────────────────────────────────
    if analysis.get("source") == "claude":
        st.markdown("---")
        st.subheader("🤖 Análise do Claude")
        complexity = analysis.get("project_complexity", "low")
        complexity_color = {"low": "#ff4444", "medium": "#ffaa00", "high": "#44ff44"}.get(complexity, "#888")
        complexity_label = {"low": "Baixa", "medium": "Média", "high": "Alta"}.get(complexity, complexity)

        st.markdown(f"""
        <div style="background: #1a1a2e; border-left: 4px solid #7c7cff; border-radius: 8px; padding: 20px; margin: 10px 0;">
            <p style="color:#ddd; font-style:italic; margin:0 0 12px 0;">"{analysis.get('profile_summary', '')}"</p>
            <div style="display:flex; gap:20px; flex-wrap:wrap;">
                <span style="color:#aaa;">📊 Nível: <b style="color:#fff;">{analysis.get('seniority','').upper()}</b></span>
                <span style="color:#aaa;">⏱️ Experiência: <b style="color:#fff;">{analysis.get('experience_years', 0)} ano(s)</b></span>
                <span style="color:#aaa;">🎯 Complexidade: <b style="color:{complexity_color};">{complexity_label}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if analysis.get("weaknesses"):
                st.markdown("**⚠️ Pontos a desenvolver:**")
                for w in analysis["weaknesses"][:3]:
                    st.markdown(f"- {w}")
        with col2:
            if analysis.get("red_flags"):
                st.markdown("**🚨 Red flags:**")
                for rf in analysis["red_flags"][:3]:
                    st.markdown(f"- {rf}")

    # ── Section 3: Skills para desenvolver ──────────────────────────────────
    SKIP_SKILLS = {"oop", "agile", "scrum", "communication", "teamwork", "problem solving", "neural networks"}
    visible_missing = [item for item in missing if item['skill'].lower() not in SKIP_SKILLS]
    if visible_missing:
        st.markdown("---")
        st.subheader("📈 Skills para desenvolver")
        st.caption("Baseado nas vagas que mais combinam com você:")
        for item in visible_missing:
            skill_name = item['skill'].title()
            count = item['appears_in_top_jobs']
            resource = SKILL_RESOURCES.get(skill_name, "")
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{skill_name}** — aparece em **{count}** das suas top vagas")
            with col2:
                if resource:
                    st.link_button("📚 Aprender", resource)

    # ── Section 4: Vagas encontradas ────────────────────────────────────────
    st.markdown("---")
    st.subheader(f"💼 Vagas encontradas — {country_name_disp}")
    if total_qualified > limit:
        st.caption(f"📊 {total_qualified} vagas passaram no filtro de score — mostrando as top {limit}. Aumente o slider para ver mais.")

    if not results:
        st.warning("Nenhuma vaga encontrada. Tente reduzir o score mínimo ou mudar os filtros.")
    else:
        for i, result in enumerate(results):
            job = result["job"]
            score = result["score"]
            source = job.get("source", "mock")
            job_country = job.get("country", country_code)
            color = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"

            with st.expander(
                f"{color} {job['title']} — {job['company']} | {result['score_percent']}",
                expanded=(i < 3 or f"cover_data_{i}" in st.session_state),
            ):
                # Compact 3-column metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Match", result["score_percent"])
                with col2:
                    st.metric("Salário", format_salary(
                        job.get("salary_min", 0), job.get("salary_max", 0), job_country, source,
                    ))
                with col3:
                    st.metric("Modalidade", "🌐 Remoto" if job.get("remote") else "🏢 Presencial")

                st.caption(f"📍 {job.get('location', 'N/A')}  |  👤 {job.get('seniority', 'N/A').upper()}  |  🏢 {source.upper()}")
                st.markdown(f"*{result['reason']}*")

                red_flags = detect_job_red_flags(job)
                if red_flags:
                    with st.expander(f"🚩 {len(red_flags)} red flag(s) detectado(s)", expanded=False):
                        for flag in red_flags:
                            st.markdown(flag)

                # Checkbox para comparar
                is_comparing = any(j["id"] == job.get("id") for j in st.session_state.compare_jobs)
                if st.checkbox("Adicionar à comparação", key=f"compare_{i}", value=is_comparing):
                    if not is_comparing:
                        st.session_state.compare_jobs.append({
                            "id": job.get("id"),
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "score": result.get("score_percent"),
                            "hiring_prob": f"{int(result.get('hiring_probability', 0) * 100)}%",
                            "matched": result.get("matched_skills", []),
                            "missing": result.get("missing_skills", []),
                            "salary": format_salary(job.get("salary_min", 0), job.get("salary_max", 0), job.get("country", "gb"), job.get("source", "")),
                            "remote": "🌐 Remoto" if job.get("remote") else "🏢 Presencial",
                            "seniority": job.get("seniority", "").upper(),
                        })
                else:
                    st.session_state.compare_jobs = [j for j in st.session_state.compare_jobs if j["id"] != job.get("id")]

                if result["matched_skills"]:
                    st.markdown("**✅ Você tem:** " + "  ".join([f"`{s}`" for s in result["matched_skills"]]))
                if result["missing_skills"]:
                    st.markdown("**❌ Faltam:** " + "  ".join([f"`{s}`" for s in result["missing_skills"]]))
                if job.get("skills_enriched"):
                    st.caption("✨ Skills extraídas por IA")

                hiring_pct = int(result.get("hiring_probability", 0) * 100)
                hp_color = "#44ff44" if hiring_pct >= 60 else "#ffaa00" if hiring_pct >= 40 else "#ff4444"
                st.markdown(f'<p style="color:{hp_color}; font-size:0.9em;">🎯 Probabilidade de chamada: <b>{hiring_pct}%</b></p>', unsafe_allow_html=True)

                # Explanation — cached so it only calls Claude once per job
                if i < 3 and analysis.get("source") == "claude":
                    exp_key = f"explanation_{i}"
                    if exp_key not in st.session_state:
                        with st.spinner("🤖 Claude gerando conselho personalizado..."):
                            st.session_state[exp_key] = generate_job_explanation(analysis, job, result)
                    if st.session_state.get(exp_key):
                        st.info(f"💡 **Conselho do Claude:** {st.session_state[exp_key]}")

                if job.get("url") and job.get("url").startswith("http") and job.get("source") != "mock":
                    st.link_button("🔗 Ver vaga completa", job["url"])
                elif job.get("source") == "mock":
                    st.caption("🔒 Vaga demonstrativa — sem link disponível")

                # Botão de aplicação
                job_id = job.get("id", f"job_{i}")
                already_applied = any(
                    j.get("job_id", j.get("id")) == job_id
                    for j in st.session_state.applied_jobs
                )

                if already_applied:
                    st.success("✅ Você já aplicou para essa vaga!")
                else:
                    if st.button("🚀 Apliquei para essa vaga", key=f"apply_{i}"):
                        if save_application(job, result):
                            st.session_state.applied_jobs = load_applications()
                        else:
                            st.session_state.applied_jobs.append({
                                "id": job_id,
                                "job_id": job_id,
                                "job_title": job.get("title"),
                                "title": job.get("title"),
                                "company": job.get("company"),
                                "score": result.get("score_percent"),
                                "hiring_prob": f"{int(result.get('hiring_probability', 0) * 100)}%",
                                "applied_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            })
                        st.rerun()

                original_input = st.text_area(
                    "Cole sua carta atual aqui (opcional — para análise e reescrita):",
                    key=f"original_letter_{i}",
                    height=120,
                    placeholder="Opcional: cole uma carta existente para receber pontuação, análise de problemas e duas versões melhoradas...",
                )
                if st.button("✉️ Gerar Cover Letter", key=f"cover_btn_{i}"):
                    with st.spinner("✍️ Claude analisando e escrevendo..."):
                        cover_data = generate_cover_letter_v2(
                            analysis, job,
                            matched_skills=result.get("matched_skills"),
                            original_letter=original_input.strip() or None,
                        )
                    if cover_data.get("version_a"):
                        st.session_state[f"cover_data_{i}"] = cover_data
                        st.session_state[f"cover_original_{i}"] = original_input.strip()
                    else:
                        st.warning("Não foi possível gerar o cover letter. Tente novamente.")

                # Botão de sugestões de melhoria
                improve_key = f"improve_text_{i}"
                if st.button("✍️ Melhorar currículo para essa vaga", key=f"improve_btn_{i}"):
                    with st.spinner("🔍 Claude analisando seu currículo vs a vaga..."):
                        suggestions = suggest_resume_improvements(analysis, job, final_text)
                    if suggestions:
                        st.session_state[improve_key] = suggestions
                        st.session_state["improve_job_index"] = i
                        st.session_state["improve_job_title"] = job.get("title", "")
                    else:
                        st.warning("Não foi possível gerar sugestões. Tente novamente.")

                if st.button("🎯 Gerar currículo para essa vaga", key=f"gen_resume_{i}"):
                    with st.spinner("🎯 Claude otimizando seu currículo para essa vaga..."):
                        new_resume = generate_full_resume(analysis, final_text, job)
                    if new_resume:
                        st.session_state["generated_resume"] = new_resume
                        st.session_state["generated_resume_job"] = job.get("title", "")
                        st.rerun()

    # ── Comparador de vagas ──────────────────────────────────────────────────
    if len(st.session_state.compare_jobs) >= 2:
        st.markdown("---")
        st.subheader(f"⚖️ Comparando {len(st.session_state.compare_jobs)} vagas")
        cols = st.columns(len(st.session_state.compare_jobs))
        for idx, cjob in enumerate(st.session_state.compare_jobs):
            with cols[idx]:
                st.markdown(f"**{cjob['title']}**")
                st.markdown(f"🏢 {cjob['company']}")
                st.markdown(f"📊 Match: **{cjob['score']}**")
                st.markdown(f"🎯 Prob: **{cjob['hiring_prob']}**")
                st.markdown(f"💰 {cjob['salary']}")
                st.markdown(f"📍 {cjob['remote']}")
                st.markdown(f"👤 {cjob['seniority']}")
                if cjob['matched']:
                    st.markdown("✅ " + ", ".join(cjob['matched'][:3]))
                if cjob['missing']:
                    st.markdown("❌ " + ", ".join(cjob['missing'][:3]))
        if st.button("🗑️ Limpar comparação"):
            st.session_state.compare_jobs = []
            st.rerun()
    elif len(st.session_state.compare_jobs) == 1:
        st.info("➕ Selecione mais uma vaga para comparar")

    # ── Section 5: Cover Letters (only if any exist) ─────────────────────────
    cover_indices = sorted(
        [int(k.split("_")[-1]) for k in st.session_state if k.startswith("cover_data_")]
    )
    if cover_indices:
        st.markdown("---")
        st.subheader("✉️ Cover Letters")
        for idx in cover_indices:
            data      = st.session_state[f"cover_data_{idx}"]
            job_r     = results[idx]["job"] if idx < len(results) else {}
            job_title = job_r.get("title", f"Vaga {idx + 1}")
            company   = job_r.get("company", "")

            with st.expander(f"✉️ {job_title} — {company}", expanded=True):
                if data.get("score") is not None:
                    score = data["score"]
                    sc = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                    st.markdown(f"**{sc} Score da carta original: {score}/100**")
                    if data.get("key_issues"):
                        st.markdown("**⚠️ Problemas encontrados:**")
                        for issue in data["key_issues"]:
                            st.markdown(f"- {issue}")
                    if data.get("recruiter_perspective"):
                        st.info(f"👔 **Perspectiva do recrutador:** {data['recruiter_perspective']}")
                    st.markdown("---")

                tab_a, tab_b = st.tabs(["✨ Versão A — Profissional", "🚀 Versão B — Ousada"])

                with tab_a:
                    st.text_area(label="", value=data["version_a"], height=280, key=f"cover_area_a_{idx}")
                    st.caption("📋 Copie o texto abaixo para manter a formatação:")
                    st.code(data["version_a"], language=None)
                    if st.button("🔄 Regenerar", key=f"regen_a_{idx}"):
                        with st.spinner("✍️ Regenerando..."):
                            new_data = generate_cover_letter_v2(
                                st.session_state["last_analysis"], job_r,
                                matched_skills=results[idx].get("matched_skills") if idx < len(results) else None,
                                original_letter=st.session_state.get(f"cover_original_{idx}") or None,
                            )
                        if new_data.get("version_a"):
                            st.session_state[f"cover_data_{idx}"] = new_data
                            st.rerun()

                with tab_b:
                    st.text_area(label="", value=data["version_b"], height=280, key=f"cover_area_b_{idx}")
                    st.caption("📋 Copie o texto abaixo para manter a formatação:")
                    st.code(data["version_b"], language=None)
                    if st.button("🔄 Regenerar", key=f"regen_b_{idx}"):
                        with st.spinner("✍️ Regenerando..."):
                            new_data = generate_cover_letter_v2(
                                st.session_state["last_analysis"], job_r,
                                matched_skills=results[idx].get("matched_skills") if idx < len(results) else None,
                                original_letter=st.session_state.get(f"cover_original_{idx}") or None,
                            )
                        if new_data.get("version_a"):
                            st.session_state[f"cover_data_{idx}"] = new_data
                            st.rerun()

                if data.get("what_improved"):
                    st.markdown("---")
                    st.markdown("**✅ O que foi melhorado:**")
                    for item in data["what_improved"]:
                        st.markdown(f"- {item}")

                if st.button("🗑️ Remover", key=f"remove_cover_{idx}"):
                    del st.session_state[f"cover_data_{idx}"]
                    st.session_state.pop(f"cover_original_{idx}", None)
                    st.rerun()

    # ── Section 6: Sugestões de melhoria de currículo ────────────────────────
    active_improve = st.session_state.get("improve_job_index")
    if active_improve is not None:
        improve_text = st.session_state.get(f"improve_text_{active_improve}", "")
        improve_title = st.session_state.get("improve_job_title", "")
        if improve_text:
            st.markdown("---")
            st.markdown(f"**✍️ Sugestões para melhorar seu currículo para: {improve_title}**")
            st.markdown(improve_text)
            st.caption("💡 Aplique essas melhorias no seu currículo antes de se candidatar!")
            if st.button("🗑️ Fechar sugestões", key="close_improve"):
                del st.session_state["improve_job_index"]
                st.rerun()
