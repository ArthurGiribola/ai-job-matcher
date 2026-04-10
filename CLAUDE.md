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
    resume_analyzer.py     # Claude Haiku structured resume analysis + explanation engine
    job_collector.py       # Adzuna + Remotive API integration + mock fallback
    hiring_predictor.py    # Logistic Regression hiring probability model
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
- Phase 3 DONE: Hiring probability (Logistic Regression) — exibe "Probabilidade de chamada: X%"
- Phase 4 DONE: Explanation engine — Claude gera conselho personalizado para top 3 vagas
- Phase 5 DONE:
  - Cache persistente com TTL de 1 hora por país (jobs_cache_{country}_meta.json)
  - st.cache_data com TTL de 30 minutos no Streamlit (cached_get_jobs)
  - Enriquecimento de vagas com Claude Haiku (enrich_jobs_with_claude, max 8/busca)
  - Botão "Apliquei para essa vaga" + histórico na sidebar (session_state)
- Cover letter gerado pelo Claude para cada vaga
- Scoring engine: 40% semantic + 20% seniority + 15% recency + 15% filters + 10% bonus
- 3 fontes de vagas: Adzuna + Remotive + mock fallback
- Lazy-loading de credenciais para funcionar no Streamlit Cloud (st.secrets)
- Cartão visual de perfil após upload do PDF
- Progress steps durante análise (em vez de spinner único)
- Card estilizado da análise do Claude (seniority, experiência, complexidade)
- Filtro de skills genéricas na seção "Skills para aprender" (OOP, Agile etc.)
- Retry automático com query genérica se Adzuna retornar 0 vagas
- Contador de vagas qualificadas vs exibidas
- Links inválidos/mock ocultados corretamente
- Descrição das vagas aumentada de 500 para 2000 chars
- Skills GCP, Azure, LLM, TensorFlow, PyTorch adicionadas ao SKILL_RESOURCES
- 31 testes passando

## Deploy
- URL: https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app
- Secrets configurados no Streamlit Cloud: ANTHROPIC_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
- Arquivo de exemplo: .streamlit/secrets.toml.example

## Decisões de arquitetura
- Frontend Streamlit é STANDALONE — não chama FastAPI, importa serviços diretamente
- Embedder usa lazy loading — modelo carrega apenas na primeira chamada
- Claude analyzer tem fallback para parser básico se API indisponível
- Credenciais lidas lazily dentro das funções (não no topo do módulo) para compatibilidade com Streamlit Cloud

## Próximo passo — Phase 6
- Autenticação de usuários (Supabase ou Auth0)
- Histórico persistente entre sessões (hoje some ao fechar)
- Alertas de novas vagas compatíveis

## Fases futuras
- Phase 7: Frontend React
- Phase 8: Production readiness (monitoring, CI/CD, Redis cache)

## Problemas conhecidos
- Histórico de aplicações some ao fechar o browser (session_state não persiste)

## Testes
- 31 testes passando em tests/
- Rodar com: python -m pytest tests/ -q

## Regras do projeto
- Nunca hardcodar API keys no código-fonte
- Sempre rodar testes após mudar scoring_engine.py ou resume_parser.py
- Frontend Streamlit deve permanecer standalone (sem dependência do FastAPI)
- Todos os novos serviços vão em app/services/
- Commit após cada feature funcionando
