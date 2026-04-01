# AI Job Matcher — Contexto do Projeto

## Stack
- FastAPI + Streamlit + sentence-transformers + Claude Haiku + Adzuna API
- Python 3.11, sentence-transformers (all-MiniLM-L6-v2), claude-haiku-4-5-20251001
- Deploy: Streamlit Cloud (frontend), local (backend)

## Estrutura do projeto
```
app/
  main.py                  # FastAPI app, 6 endpoints
  services/
    embedder.py            # sentence-transformers embeddings + cosine similarity
    scoring_engine.py      # weighted scoring (semantic + seniority + recency)
    resume_parser.py       # PDF text extraction + basic skill extraction
    resume_analyzer.py     # Claude Haiku structured resume analysis
    job_collector.py       # Adzuna API integration + mock fallback
frontend/
  app.py                   # Streamlit UI (standalone, no FastAPI dependency)
data/
  mock_jobs.json           # 20 Brazilian tech jobs for fallback
tests/
  test_scoring.py          # 23 unit tests, all passing
  test_embedder.py         # embedding validation tests
  test_resume_analyzer.py  # Claude integration tests
```

## O que está feito
- Phase 1 DONE: Embeddings semânticos (all-MiniLM-L6-v2) substituindo Jaccard
- Phase 2 DONE: Extração estruturada com Claude Haiku (skills com níveis, seniority, red flags)
- Scoring engine: 40% semantic + 20% seniority + 15% recency + 15% filters + 10% bonus
- Cache de vagas separado por país (jobs_cache_{country}.json)
- Lazy-loading de credenciais para funcionar no Streamlit Cloud (st.secrets)
- Cartão visual de perfil após upload do PDF
- Progress steps durante análise (em vez de spinner único)
- Card estilizado da análise do Claude (seniority, experiência, complexidade)
- Filtro de skills genéricas na seção "Skills para aprender" (OOP, Agile etc.)
- Retry automático com query genérica se Adzuna retornar 0 vagas

## Deploy
- URL: https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app
- Secrets configurados no Streamlit Cloud: ANTHROPIC_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
- Arquivo de exemplo: .streamlit/secrets.toml.example

## Decisões de arquitetura
- Frontend Streamlit é STANDALONE — não chama FastAPI, importa serviços diretamente
- Embedder usa lazy loading — modelo carrega apenas na primeira chamada
- Claude analyzer tem fallback para parser básico se API indisponível
- Credenciais lidas lazily dentro das funções (não no topo do módulo) para compatibilidade com Streamlit Cloud

## Próximo passo — Phase 3
Implementar previsão de probabilidade de contratação:
- Features: semantic_score, skill_coverage, seniority_gap, experience_years_gap
- Modelo simples (Logistic Regression)
- Dados sintéticos gerados pelo Claude para treino
- Output: hiring_probability 0.0 → 1.0
- Mostrar no card da vaga como "Probabilidade de chamada: 73%"

## Fases futuras
- Phase 4: Motor de explicação mais rico usando skill levels do Claude
- Phase 5: Autenticação + perfis de usuário + histórico de buscas
- Phase 6: Frontend React
- Phase 7: Production readiness (monitoring, CI/CD, Redis cache)

## Problemas conhecidos
- Cache não persiste entre reboots do Streamlit Cloud
- Descrição das vagas truncada em 500 chars (aumentar para 2000)

## Testes
- 23 testes passando em tests/
- Rodar com: python -m pytest tests/ -q

## Regras do projeto
- Nunca hardcodar API keys no código-fonte
- Sempre rodar testes após mudar scoring_engine.py ou resume_parser.py
- Frontend Streamlit deve permanecer standalone (sem dependência do FastAPI)
- Todos os novos serviços vão em app/services/
- Commit após cada feature funcionando
