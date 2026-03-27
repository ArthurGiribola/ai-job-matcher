# 🚀 AI Career Intelligence Platform

An AI-powered system that analyzes resumes, matches candidates with job opportunities, and predicts hiring probability.

---

## 🧠 Overview

This project was built to solve a real problem:

> ❌ Candidates don’t know why they get rejected  
> ❌ Job matching platforms are shallow and generic  

✅ This system provides **deep insights**, not just scores.

---

## 🔥 Key Features

- 📄 Resume Analysis (PDF/TXT)
- 🎯 Job Matching Engine
- 📊 Compatibility Score (Jaccard Similarity)
- 📉 Skill Gap Detection
- 🧠 Hiring Probability Estimation *(coming soon)*
- ✨ AI Resume Optimization *(coming soon)*

---

## ⚙️ How It Works

1. Extract skills from the resume
2. Compare with job requirements
3. Calculate similarity score
4. Rank jobs by relevance
5. Identify missing skills

---

## 🏗️ Tech Stack

**Backend**
- Python 3.11+
- FastAPI

**Data Processing**
- JSON (mock jobs)
- Custom scoring algorithm

**Future AI**
- NLP (spaCy)
- Machine Learning models

---

## 📊 Example Output

```json
{
  "job": "Backend Python",
  "score": 0.78,
  "reason": "Strong match in Python and FastAPI",
  "missing_skills": ["PostgreSQL"]
}
