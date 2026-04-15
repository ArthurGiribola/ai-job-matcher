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

## O que está feito (atualizado — 15/04/2026)
- Phases 1-7 DONE completas
- 6 bugs críticos corrigidos (auditoria 1)
- 12 bugs corrigidos (auditoria 2)
- Código morto removido (spacy, semantic_similarity, cover_letter v1)
- safe_num() para score de mercado
- experience_years passado ao predictor
- warmup_mock_jobs removido
- intern adicionado ao SENIORITY_LEVELS
- Nome do candidato extraído no EXTRACTION_PROMPT
- Jooble API key movida para header
- Cache não persiste mais 0 vagas
- Testes limpados — sem chamadas globais à API

## Deploy
- URL: https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app
- Secrets configurados no Streamlit Cloud: ANTHROPIC_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
- Arquivo de exemplo: .streamlit/secrets.toml.example

## Decisões de arquitetura
- Frontend Streamlit é STANDALONE — não chama FastAPI, importa serviços diretamente
- Embedder usa lazy loading — modelo carrega apenas na primeira chamada
- Claude analyzer tem fallback para parser básico se API indisponível
- Credenciais lidas lazily dentro das funções (não no topo do módulo) para compatibilidade com Streamlit Cloud

## Próximo passo — o que fazer na próxima sessão (em ordem)
1. Feedback loop nas candidaturas — adicionar status: "Apliquei", "Fui chamado", "Fiz entrevista", "Recebi oferta", "Não responderam" — requer ALTER TABLE no Supabase e update_application_status() no database.py
2. Aviso no modelo de probabilidade — deixar claro que é estimativa
3. Refatoração do frontend — quebrar app.py em módulos
4. Autenticação real com Supabase Auth
5. Melhoria de UX geral

## Bugs restantes conhecidos
- fetch_muse_jobs category param incorreto
- Session ID no URL — privacy risk
- 16 funções sem testes
- Cache de arquivo inútil no Streamlit Cloud

## Testes
- Rodar com: python -m pytest tests/test_resume_analyzer.py -q (6 passando)
- test_scoring.py e test_embedder.py bloqueados por Application Control do Windows (DLL issue — não é bug do código)

## Regras do projeto
- Nunca hardcodar API keys no código-fonte
- Sempre rodar testes após mudar scoring_engine.py ou resume_parser.py
- Frontend Streamlit deve permanecer standalone (sem dependência do FastAPI)
- Todos os novos serviços vão em app/services/
- Commit após cada feature funcionando
