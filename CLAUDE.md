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
- Cover letter gerado pelo Claude para cada vaga
- Scoring engine: 40% semantic + 20% seniority + 15% recency + 15% filters + 10% bonus
- Remotive API integrada como terceira fonte de vagas (gratuita, sem chave)
- Cache de vagas separado por país (jobs_cache_{country}.json)
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

## Deploy
- URL: https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app
- Secrets configurados no Streamlit Cloud: ANTHROPIC_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
- Arquivo de exemplo: .streamlit/secrets.toml.example

## Decisões de arquitetura
- Frontend Streamlit é STANDALONE — não chama FastAPI, importa serviços diretamente
- Embedder usa lazy loading — modelo carrega apenas na primeira chamada
- Claude analyzer tem fallback para parser básico se API indisponível
- Credenciais lidas lazily dentro das funções (não no topo do módulo) para compatibilidade com Streamlit Cloud

## Próximo passo — Phase 5
- Persistent cache (Redis ou banco simples) — cache some entre reboots no Streamlit Cloud
- Logging estruturado — saber quando Claude falha em produção
- Explanation engine em português consistente

## Fases futuras
- Phase 6: Autenticação + perfis de usuário + histórico de buscas
- Phase 7: Frontend React
- Phase 8: Production readiness (monitoring, CI/CD, Redis cache)

## Problemas conhecidos
- Cache não persiste entre reboots do Streamlit Cloud

## Testes
- 23 testes passando em tests/
- Rodar com: python -m pytest tests/ -q

## Regras do projeto
- Nunca hardcodar API keys no código-fonte
- Sempre rodar testes após mudar scoring_engine.py ou resume_parser.py
- Frontend Streamlit deve permanecer standalone (sem dependência do FastAPI)
- Todos os novos serviços vão em app/services/
- Commit após cada feature funcionando
