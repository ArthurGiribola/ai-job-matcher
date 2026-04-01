# 🎯 AI Job Matcher

> AI-powered system that analyzes resumes, matches candidates with real job opportunities, and identifies skill gaps — built with Python, FastAPI, NLP, and Streamlit.

---

## 🚀 Live Demo

> Upload your resume (PDF or text) → Get ranked job matches with compatibility scores → See exactly what skills you're missing

---

## 🧠 What it does

Most job platforms show you jobs. This system tells you **why** you match or don't — and what to do about it.

- 📄 **Resume Analysis** — Upload PDF or paste text, extracts 18+ skills automatically
- 🎯 **Job Matching** — Ranks jobs by real compatibility score (not keyword stuffing)
- 📊 **Skill Gap Detection** — Shows exactly what's missing for your top matches
- ⭐ **Strengths Highlight** — Identifies your high-value skills (AWS, ML, Docker, etc.)
- 🔗 **Direct Apply Links** — One click to apply on Gupy or LinkedIn

---

## 📊 Scoring Algorithm

The match score is calculated across 5 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Skills compatibility | 40% | Jaccard similarity between resume and job skills |
| Seniority match | 20% | Penalizes over/under-qualified matches |
| Job recency | 15% | Exponential decay for older postings |
| Filter adherence | 15% | Remote, location, salary preferences |
| High-value skill bonus | 10% | AWS, ML, Docker, LLM, etc. |

---

## 🏗️ Architecture
```
User (PDF/Text)
      ↓
Streamlit Frontend (port 8501)
      ↓
FastAPI Backend (port 8000)
      ↓
┌─────────────────────────────┐
│  ResumeParserService        │  ← pdfminer.six + spaCy
│  SkillExtractorService      │  ← Custom dictionary (300+ skills)
│  ScoringEngine              │  ← Weighted scoring algorithm
└─────────────────────────────┘
      ↓
JSON Response with ranked jobs + gaps
```

---

## ⚙️ Tech Stack

**Backend:** Python 3.11+, FastAPI, Pydantic, Uvicorn

**NLP & AI:** spaCy, pdfminer.six, Custom skill dictionary

**Frontend:** Streamlit

**Data:** JSON mock jobs (Gupy/LinkedIn format) → Real API integration coming

---

## 🚀 Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/ArthurGiribola/ai-job-matcher.git
cd ai-job-matcher

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Start the API
uvicorn app.main:app --reload

# 6. Start the interface (new terminal)
python -m streamlit run frontend/app.py
```

Open `http://localhost:8501` and upload your resume.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/jobs` | List all available jobs |
| POST | `/match` | Match skills against jobs |
| POST | `/match/quick` | Quick match with skill list |
| POST | `/resume/analyze-text` | Analyze resume text |
| POST | `/resume/upload` | Upload and analyze PDF |
| POST | `/resume/analyze-and-match` | Full pipeline in one call |

Full docs available at `http://localhost:8000/docs`

---

## 📁 Project Structure
```
ai-job-matcher/
├── app/
│   ├── main.py                 # FastAPI app + endpoints
│   └── services/
│       ├── scoring_engine.py   # Match scoring algorithm
│       └── resume_parser.py    # PDF parser + skill extractor
├── data/
│   └── mock_jobs.json          # 20 real Brazilian tech jobs
├── frontend/
│   └── app.py                  # Streamlit interface
├── requirements.txt
└── README.md
```

---

## 🗺️ Roadmap

- [x] Resume parser (PDF + text)
- [x] Skill extraction with NLP
- [x] Scoring engine with 5 dimensions
- [x] REST API with FastAPI
- [x] Visual interface with Streamlit
- [x] PDF upload directly in UI
- [ ] Real job API integration (Gupy, Adzuna)
- [ ] Deploy on cloud (Railway + Streamlit Cloud)
- [ ] Resume rewrite suggestions per job
- [ ] Career evolution dashboard

---

## 👤 Author

**Arthur Giribola**
- LinkedIn: [linkedin.com/in/arthurgiribola](https://linkedin.com/in/arthurgiribola)
- GitHub: [github.com/ArthurGiribola](https://github.com/ArthurGiribola)

---

## 📄 License

MIT License