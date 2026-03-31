import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Job Matcher",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Job Matcher")
st.markdown("Cole seu currículo abaixo e descubra as vagas mais compatíveis com seu perfil.")

with st.sidebar:
    st.header("⚙️ Filtros")
    seniority = st.selectbox("Nível", ["junior", "mid", "senior", "lead"])
    remote_only = st.checkbox("Apenas vagas remotas", value=True)
    min_score = st.slider("Score mínimo", 0, 100, 40) / 100
    limit = st.slider("Número de vagas", 5, 20, 10)

st.markdown("---")

resume_text = st.text_area(
    "📄 Cole o texto do seu currículo aqui:",
    height=200,
    placeholder="Cole aqui o conteúdo do seu currículo em texto..."
)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_btn = st.button("🔍 Analisar e Buscar Vagas", type="primary", use_container_width=True)

if analyze_btn:
    if not resume_text or len(resume_text) < 50:
        st.error("Por favor, cole o texto do seu currículo antes de analisar.")
    else:
        with st.spinner("Analisando seu currículo e buscando vagas..."):
            try:
                params = {
                    "text": resume_text,
                    "seniority": seniority
                }
                response = requests.post(f"{API_URL}/resume/analyze-and-match", params=params)

                if response.status_code == 200:
                    data = response.json()
                    profile = data["profile"]
                    results = data["results"]
                    missing = data["top_missing_skills"]

                    # Filtra por remoto se necessário
                    if remote_only:
                        results = [r for r in results if r["job"].get("remote")]

                    # Filtra por score mínimo
                    results = [r for r in results if r["score"] >= min_score]

                    # Limita quantidade
                    results = results[:limit]

                    st.success(f"✅ Currículo analisado! {profile['total_skills']} skills encontradas.")

                    # PERFIL DO CANDIDATO
                    st.markdown("---")
                    st.subheader("👤 Seu Perfil")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Skills encontradas", profile["total_skills"])
                    with col2:
                        st.metric("Nível detectado", profile["seniority"].upper())
                    with col3:
                        st.metric("Vagas compatíveis", len(results))

                    # SKILLS
                    st.markdown("**🛠️ Skills identificadas:**")
                    skills_text = "  ".join([f"`{s}`" for s in profile["skills"]])
                    st.markdown(skills_text)

                    if profile.get("strengths"):
                        st.markdown("**⭐ Pontos fortes:**")
                        strengths_text = "  ".join([f"`{s}`" for s in profile["strengths"]])
                        st.markdown(strengths_text)

                    # GAPS
                    if missing:
                        st.markdown("---")
                        st.subheader("📈 Skills para aprender (aparecem nas melhores vagas)")
                        for item in missing:
                            st.markdown(f"- **{item['skill'].title()}** — aparece em {item['appears_in_top_jobs']} vagas do seu top")

                    # VAGAS
                    st.markdown("---")
                    st.subheader(f"💼 Top {len(results)} vagas para você")

                    if not results:
                        st.warning("Nenhuma vaga encontrada com os filtros selecionados. Tente reduzir o score mínimo.")
                    else:
                        for i, result in enumerate(results):
                            job = result["job"]
                            score = result["score"]
                            color = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"

                            with st.expander(f"{color} {job['title']} — {job['company']} | {result['score_percent']}", expanded=(i < 3)):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Match", result["score_percent"])
                                with col2:
                                    st.metric("Salário", f"R${job['salary_min']:,} – R${job['salary_max']:,}")
                                with col3:
                                    remote_label = "🌐 Remoto" if job["remote"] else "🏢 Presencial"
                                    st.metric("Modalidade", remote_label)

                                st.markdown(f"📍 {job['location']} | 👤 {job['seniority'].upper()}")
                                st.markdown(f"*{result['reason']}*")

                                if result["matched_skills"]:
                                    matched = "  ".join([f"`{s}`" for s in result["matched_skills"]])
                                    st.markdown(f"**✅ Você tem:** {matched}")

                                if result["missing_skills"]:
                                    missing_skills = "  ".join([f"`{s}`" for s in result["missing_skills"]])
                                    st.markdown(f"**❌ Faltam:** {missing_skills}")

                                st.link_button("🔗 Ver vaga completa", job["url"])

                else:
                    st.error(f"Erro na API: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ API não está rodando. Inicie o servidor com: uvicorn app.main:app --reload")
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")