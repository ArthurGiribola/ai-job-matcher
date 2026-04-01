import streamlit as st
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_parser import extract_text_from_pdf
from app.services.resume_analyzer import analyze_resume, get_skill_names
from app.services.job_collector import get_jobs, SUPPORTED_COUNTRIES
from app.services.scoring_engine import rank_jobs, get_top_missing_skills

SKILL_RESOURCES = {
    "Docker": "https://docs.docker.com/get-started/",
    "Kubernetes": "https://kubernetes.io/docs/tutorials/",
    "Aws": "https://aws.amazon.com/training/",
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
    else:
        currency = CURRENCY_BY_COUNTRY.get(country_code, "£")
    if not salary_min and not salary_max:
        return "Não informado"
    if salary_max:
        return f"{currency} {salary_min:,.0f} – {salary_max:,.0f}"
    return f"{currency} {salary_min:,.0f}+"


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
            update_progress("Claude está analisando seu perfil...", "🤖")

            # Análise com Claude
            analysis = analyze_resume(final_text)
            profile = {
                "skills": get_skill_names(analysis),
                "total_skills": len(analysis.get("skills", [])),
                "seniority": analysis.get("seniority", "junior"),
                "strengths": analysis.get("strengths", []),
                "source": analysis.get("source", "fallback"),
            }

            update_progress("Buscando vagas compatíveis no mundo...", "🌍")
            jobs = get_jobs(
                candidate_skills=profile["skills"],
                limit=40,
                country=country_code,
                location=city.strip() if city else "",
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
            results = [r for r in results if r["score"] >= min_score]
            results = results[:limit]

            st.success(f"✅ {profile['total_skills']} skills encontradas. Análise via {'Claude AI' if analysis.get('source') == 'claude' else 'parser básico'}.")

            # PERFIL
            st.markdown("---")
            st.subheader("👤 Seu Perfil")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Skills encontradas", profile["total_skills"])
            with col2:
                st.metric("Nível detectado", profile["seniority"].upper())
            with col3:
                st.metric("Vagas analisadas", len(jobs))
            with col4:
                st.metric("Matches encontrados", len(results))

            st.markdown("**🛠️ Skills identificadas:**")
            st.markdown("  ".join([f"`{s}`" for s in profile["skills"]]))

            if profile.get("strengths"):
                st.markdown("**⭐ Pontos fortes:**")
                st.markdown("  ".join([f"`{s}`" for s in profile["strengths"][:5]]))

            # ANÁLISE CLAUDE
            if analysis.get("source") == "claude":
                st.markdown("---")
                complexity = analysis.get("project_complexity", "low")
                complexity_color = {"low": "#ff4444", "medium": "#ffaa00", "high": "#44ff44"}.get(complexity, "#888")
                complexity_label = {"low": "Baixa", "medium": "Média", "high": "Alta"}.get(complexity, complexity)

                st.markdown(f"""
                <div style="background: #1a1a2e; border-left: 4px solid #7c7cff; border-radius: 8px; padding: 20px; margin: 10px 0;">
                    <h4 style="color:#7c7cff; margin:0 0 10px 0;">🤖 Análise do Claude</h4>
                    <p style="color:#ddd; font-style:italic;">"{analysis.get('profile_summary', '')}"</p>
                    <hr style="border-color:#333; margin: 12px 0;">
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

            # SKILLS PARA APRENDER
            if missing:
                st.markdown("---")
                st.subheader("📈 Skills para aprender")
                st.markdown("Baseado nas vagas que mais combinam com você:")
                SKIP_SKILLS = {"oop", "agile", "scrum", "communication", "teamwork", "problem solving", "neural networks"}
                for item in missing:
                    skill_name = item['skill'].title()
                    if item['skill'].lower() in SKIP_SKILLS:
                        continue
                    count = item['appears_in_top_jobs']
                    resource = SKILL_RESOURCES.get(skill_name, "")
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{skill_name}** — aparece em **{count}** das suas top vagas")
                    with col2:
                        if resource:
                            st.link_button("📚 Aprender", resource)

            # VAGAS
            st.markdown("---")
            st.subheader(f"💼 Top {len(results)} vagas para você em {country_name}")

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
                        expanded=(i < 3)
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Match", result["score_percent"])
                        with col2:
                            salary_str = format_salary(
                                job.get("salary_min", 0),
                                job.get("salary_max", 0),
                                job_country,
                                source,
                            )
                            st.markdown("**Salário**")
                            st.markdown(f"### {salary_str}")
                        with col3:
                            st.metric("Modalidade", "🌐 Remoto" if job.get("remote") else "🏢 Presencial")

                        st.markdown(f"📍 **{job.get('location', 'N/A')}** | 👤 **{job.get('seniority', 'N/A').upper()}** | 🏢 {source.upper()}")
                        st.markdown(f"*{result['reason']}*")

                        if result["matched_skills"]:
                            st.markdown("**✅ Você tem:** " + "  ".join([f"`{s}`" for s in result["matched_skills"]]))
                        if result["missing_skills"]:
                            st.markdown("**❌ Faltam:** " + "  ".join([f"`{s}`" for s in result["missing_skills"]]))
                        hiring_pct = int(result.get("hiring_probability", 0) * 100)
                        color = "#44ff44" if hiring_pct >= 60 else "#ffaa00" if hiring_pct >= 40 else "#ff4444"
                        st.markdown(f'<p style="color:{color}; font-size:0.9em;">🎯 Probabilidade de chamada: <b>{hiring_pct}%</b></p>', unsafe_allow_html=True)

                        if job.get("url") and job.get("url").startswith("http") and job.get("source") != "mock":
                            st.link_button("🔗 Ver vaga completa", job["url"])
                        elif job.get("source") == "mock":
                            st.caption("🔒 Vaga demonstrativa — sem link disponível")

        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
            st.exception(e)
