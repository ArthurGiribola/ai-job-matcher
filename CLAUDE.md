# AI Job Matcher — Project Context for Claude Code

## What is this project
A semantic AI job matching system that analyzes resumes and ranks real job opportunities by compatibility. Built as a portfolio project evolving into a real SaaS product.

## Current Stack
- Backend: Python 3.11, FastAPI, Uvicorn
- AI Layer: sentence-transformers (all-MiniLM-L6-v2), Claude Haiku API (Anthropic)
- Job Data: Adzuna API + mock jobs (data/mock_jobs.json)
- Frontend: Streamlit
- Deploy: Streamlit Cloud (frontend), local (backend)

## Project Structure
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

## What is implemented and working
- Phase 1 DONE: Semantic embeddings with sentence-transformers replacing Jaccard similarity
- Phase 2 DONE: Claude Haiku extracts structured profile (skills with levels, real seniority, red flags)
- Scoring engine: 40% semantic + 20% seniority + 15% recency + 15% filters + 10% bonus
- Adzuna API: fetches real jobs by country/city
- Streamlit UI: PDF upload, country filter, skill gap analysis, job ranking
- Deploy: https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app

## Current problems to fix
1. ANTHROPIC_API_KEY not being read correctly in Streamlit Cloud (falls back to basic parser)
2. Adzuna returning 0 results in Cloud (credentials not loading)
3. Mock jobs showing R$ currency even when UK is selected
4. Embeddings recalculated on every request (no caching) — performance issue

## Environment variables needed
- ANTHROPIC_API_KEY
- ADZUNA_APP_ID
- ADZUNA_APP_KEY

## Architecture decisions made
- Streamlit frontend is STANDALONE — does not call FastAPI, imports services directly
- Embedder uses lazy loading — model loads only on first call
- Claude analyzer has fallback to basic parser if API unavailable
- Job collector uses Adzuna for real data + mock_jobs.json as fallback

## Next phases planned
- Phase 3: Score calibration with user feedback
- Phase 4: Richer explanation engine using Claude skill levels
- Phase 5: Authentication + user profiles + search history
- Phase 6: React frontend
- Phase 7: Production readiness (monitoring, CI/CD, Redis cache)

## Rules for this project
- Never hardcode API keys in source code
- Always run tests after changing scoring_engine.py or resume_parser.py
- Keep Streamlit frontend standalone (no FastAPI dependency)
- All new services go in app/services/
- Commit after each working feature
