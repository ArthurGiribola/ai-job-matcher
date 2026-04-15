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

## O que está feito (atualizado)
- Phase 1 DONE: Embeddings semânticos (all-MiniLM-L6-v2)
- Phase 2 DONE: Extração estruturada com Claude Haiku
- Phase 3 DONE: Hiring probability (Logistic Regression)
- Phase 4 DONE: Explanation engine para top 3 vagas
- Phase 5 DONE: Cache persistente + enriquecimento de vagas + botão "Apliquei"
- Phase 6 DONE: Supabase + sugestões de melhoria + validação de qualidade + cover letter
- Phase 7 DONE: Geração de currículo profissional completo
- Features extras: score de mercado, red flags, comparador de vagas, tradução para inglês, badges coloridos por fonte
- 5 fontes de vagas: Adzuna, Remotive, Reed, Jooble, The Muse
- Histórico persistente via Supabase + session_id via query params
- UI polida com badges, pills, layout profissional
- README profissional no GitHub
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

## Próximo passo — Phase 8
- Autenticação de usuários
- Dashboard de progresso de carreira
- Download de currículo em PDF
- Roadmap de carreira personalizado com Claude

## Testes
- 31 testes passando em tests/
- Rodar com: python -m pytest tests/ -q

## Regras do projeto
- Nunca hardcodar API keys no código-fonte
- Sempre rodar testes após mudar scoring_engine.py ou resume_parser.py
- Frontend Streamlit deve permanecer standalone (sem dependência do FastAPI)
- Todos os novos serviços vão em app/services/
- Commit após cada feature funcionando
