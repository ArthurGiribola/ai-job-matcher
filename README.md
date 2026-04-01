# 🎯 AI Job Matcher

AI-powered system that analyzes resumes with Claude AI, matches candidates with real job opportunities using semantic embeddings, and identifies skill gaps — built with Python, FastAPI, Claude Haiku, sentence-transformers and Streamlit.

## 🚀 Live Demo
**[ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app](https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app)**

Upload your resume (PDF or text) → Claude AI extracts your profile → Get semantically ranked job matches → See exactly what skills you're missing

---

## 🧠 What it does

Most job platforms show you jobs. This system tells you **why you match or don't** — and what to do about it.

- 📄 **Resume Analysis** — Claude Haiku extracts skills with proficiency levels, seniority, red flags and project complexity
- 🎯 **Semantic Matching** — Ranks jobs using sentence-transformers embeddings (not keyword stuffing)
- 📊 **Skill Gap Detection** — Shows exactly what's missing for your top matches with learning resources
- 🌍 **Global Job Search** — Real jobs from Adzuna API across 20+ countries
- 🤖 **AI Profile Card** — Visual profile card with Claude's honest assessment of your experience level

---

## 📊 Scoring Algorithm

The match score is calculated across 5 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Semantic similarity | 40% | Cosine similarity between resume and job embeddings (all-MiniLM-L6-v2) |
| Seniority match | 20% | Penalizes over/under-qualified matches |
| Job recency | 15% | Exponential decay for older postings |
| Filter adherence | 15% | Remote, location, salary preferences |
| High-value skill bonus | 10% | AWS, ML, Docker, LLM, Kubernetes, etc. |

---

## 🏗️ Architecture
```
User (PDF/Text)
      ↓
Streamlit Frontend
      ↓
┌─────────────────────────────────────┐
│  ResumeAnalyzer (Claude Haiku)      │  ← Structured extraction
│  Embedder (sentence-transformers)   │  ← Semantic vectors
│  JobCollector (Adzuna API)          │  ← Real global jobs
│  ScoringEngine (cosine similarity)  │  ← Weighted ranking
└─────────────────────────────────────┘
      ↓
Ranked jobs + skill gaps + learning resources
```

---

## ⚙️ Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic, Uvicorn
- **AI Layer:** Claude Haiku (Anthropic), sentence-transformers (all-MiniLM-L6-v2)
- **Job Data:** Adzuna API (20+ countries)
- **Frontend:** Streamlit
- **Deploy:** Streamlit Cloud

---

## 🚀 Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/ArthurGiribola/ai-job-matcher.git
cd ai-job-matcher

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your keys:
# ANTHROPIC_API_KEY = "sk-ant-..."
# ADZUNA_APP_ID = "your_id"
# ADZUNA_APP_KEY = "your_key"

# 5. Start the interface
streamlit run frontend/app.py
```

Open `http://localhost:8501` and upload your resume.

---

## 📁 Project Structure
```
ai-job-matcher/
├── app/
│   ├── main.py                    # FastAPI app + endpoints
│   └── services/
│       ├── embedder.py            # sentence-transformers embeddings
│       ├── resume_analyzer.py     # Claude Haiku structured extraction
│       ├── resume_parser.py       # PDF parser + basic skill extractor
│       ├── job_collector.py       # Adzuna API integration
│       └── scoring_engine.py      # Semantic scoring algorithm
├── data/
│   └── mock_jobs.json             # Brazilian mock jobs fallback
├── frontend/
│   └── app.py                     # Streamlit interface
├── tests/                         # 23 passing tests
├── .streamlit/
│   └── secrets.toml.example       # Environment variables template
├── CLAUDE.md                      # Project context for Claude Code
└── README.md
```

---

## 🗺️ Roadmap

- ✅ Resume parser (PDF + text)
- ✅ Claude AI structured extraction (skills, seniority, red flags)
- ✅ Semantic embeddings matching
- ✅ Scoring engine with 5 dimensions
- ✅ REST API with FastAPI
- ✅ Streamlit UI with visual profile card
- ✅ Real job API integration (Adzuna — 20+ countries)
- ✅ Deploy on Streamlit Cloud
- ⏳ Hiring probability prediction (Phase 3)
- ⏳ Explanation engine ("why you're not getting callbacks")
- ⏳ Persistent cache (Redis)
- ⏳ Career evolution dashboard

---

## 👤 Author

**Arthur Giribola**
- LinkedIn: [linkedin.com/in/arthurgiribola](https://linkedin.com/in/arthurgiribola)
- GitHub: [github.com/ArthurGiribola](https://github.com/ArthurGiribola)

---

## 📄 License

MIT License
