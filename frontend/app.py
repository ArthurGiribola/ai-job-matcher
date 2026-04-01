import streamlit as st
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_parser import parse_resume_text, extract_text_from_pdf
from app.services.job_collector import get_jobs
from app.services.scoring_engine import rank_jobs, get_top_missing_skills

st.set_page_config(
    page_title="AI Job Matcher",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Job Matcher")
st.markdown("Envie seu currículo e descubra as vagas mais compatíveis com seu perfil.")

with st.sidebar:
    st.header("⚙️ Filtros")
    seniority = st.selectbox("Nível", ["junior", "mid", "senior", "lead"])
    remote_only = st.checkbox("Apenas vagas remotas", value=False)
    min_score = st.slider("Score mínimo", 0, 100, 40) / 100
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
                    st.success("✅ PDF processado com sucesso!")
                    st.text_area(
                        "Texto extraído (prévia):",
                        resume_text_from_pdf[:500] + "...",
                        height=150,
                        disabled=True
                    )
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
        with st.spinner("Analisando seu currículo e buscando vagas..."):
            try:
                profile = parse_resume_text(final_text)
                jobs = get_jobs(candidate_skills=profile["skills"], limit=40)
                results = rank_jobs(
                    jobs=jobs,
                    candidate_skills=profile["skills"],
                    candidate_seniority=profile.get("seniority", seniority),
                    limit=limit,
                )
                missing = get_top_missing_skills(results)

                if remote_only:
                    results = [r for r in results if r["job"].get("remote")]
                results = [r for r in results if r["score"] >= min_score]
                results = results[:limit]

                st.success(f"✅ Currículo analisado! {profile['total_skills']} skills encontradas.")

                st.markdown("---")
                st.subheader("👤 Seu Perfil")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Skills encontradas", profile["total_skills"])
                with col2:
                    st.metric("Nível detectado", profile["seniority"].upper())
                with col3:
                    st.metric("Vagas compatíveis", len(results))

                st.markdown("**🛠️ Skills identificadas:**")
                st.markdown("  ".join([f"`{s}`" for s in profile["skills"]]))

                if profile.get("strengths"):
                    st.markdown("**⭐ Pontos fortes:**")
                    st.markdown("  ".join([f"`{s}`" for s in profile["strengths"]]))

                if missing:
                    st.markdown("---")
                    st.subheader("📈 Skills para aprender")
                    for item in missing:
                        st.markdown(
                            f"- **{item['skill'].title()}** — aparece em {item['appears_in_top_jobs']} vagas do seu top"
                        )

                st.markdown("---")
                st.subheader(f"💼 Top {len(results)} vagas para você")

                if not results:
                    st.warning("Nenhuma vaga encontrada. Tente reduzir o score mínimo.")
                else:
                    for i, result in enumerate(results):
                        job = result["job"]
                        score = result["score"]
                        color = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"

                        with st.expander(
                            f"{color} {job['title']} — {job['company']} | {result['score_percent']}",
                            expanded=(i < 3)
                        ):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Match", result["score_percent"])
                            with col2:
                                salary_min = job.get("salary_min", 0) or 0
                                salary_max = job.get("salary_max", 0) or 0
                                if salary_min > 0:
                                    st.metric("Salário", f"£{salary_min:,}–£{salary_max:,}")
                                else:
                                    st.metric("Salário", "Não informado")
                            with col3:
                                st.metric("Modalidade", "🌐 Remoto" if job.get("remote") else "🏢 Presencial")

                            st.markdown(f"📍 {job.get('location', 'N/A')} | 👤 {job.get('seniority', 'N/A').upper()}")
                            st.markdown(f"*{result['reason']}*")

                            if result["matched_skills"]:
                                st.markdown("**✅ Você tem:** " + "  ".join([f"`{s}`" for s in result["matched_skills"]]))

                            if result["missing_skills"]:
                                st.markdown("**❌ Faltam:** " + "  ".join([f"`{s}`" for s in result["missing_skills"]]))

                            if job.get("url"):
                                st.link_button("🔗 Ver vaga completa", job["url"])

            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")
