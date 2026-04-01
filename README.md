# 🎯 AI Job Matcher

> Sistema de IA que analisa currículos e ranqueia vagas por compatibilidade técnica real.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🧠 O problema que resolve

Candidatos perdem horas aplicando para vagas sem saber se têm o perfil certo.
Plataformas como LinkedIn fazem matching superficial, sem considerar compatibilidade técnica real.

**Este sistema responde duas perguntas:**
- Quais vagas mais combinam comigo agora?
- O que está faltando no meu perfil para conseguir vagas melhores?

---

## 🔥 Como funciona

1. Usuário cola o texto do currículo
2. Sistema extrai skills automaticamente com NLP
3. Detecta nível de senioridade
4. Compara com 20+ vagas reais do mercado brasileiro
5. Calcula score de compatibilidade (%)
6. Retorna vagas ranqueadas com justificativa e gaps

---

## 📊 Exemplo de output real
```json
{
  "job": "Junior ML Engineer — Olist",
  "score": 0.731,
  "score_percent": "73%",
  "reason": "Bom match (73%) — você tem: Python, scikit-learn, pandas, SQL",
  "missing_skills": [],
  "salary": "R$5.000 – R$8.500"
}
```

---

## ⚙️ Como o score é calculado

| Dimensão | Peso |
|----------|------|
| Skills compatíveis (Jaccard Similarity) | 40% |
| Nível da vaga vs candidato | 20% |
| Recência da vaga | 15% |
| Aderência aos filtros | 15% |
| Bônus por skills de alto valor (AWS, ML, Docker) | 10% |

---

## 🏗️ Arquitetura
```
ai-job-matcher/
├── app/
│   ├── main.py               # API FastAPI — 6 endpoints
│   └── services/
│       ├── scoring_engine.py # Motor de scoring com 5 dimensões
│       └── resume_parser.py  # Extrator de skills com NLP
├── data/
│   └── mock_jobs.json        # 20 vagas reais do mercado BR
├── frontend/
│   └── app.py                # Interface Streamlit
└── requirements.txt
```

---

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- Git

### Instalação
```bash
# 1. Clonar o repositório
git clone https://github.com/ArthurGiribola/ai-job-matcher.git
cd ai-job-matcher

# 2. Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Instalar dependências
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Rodar a API (terminal 1)
uvicorn app.main:app --reload

# 5. Rodar a interface (terminal 2)
python -m streamlit run frontend/app.py
```

Acesse: `http://localhost:8501`

---

## 🔌 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Status da API |
| GET | `/jobs` | Lista todas as vagas |
| POST | `/match` | Ranqueia vagas por skills |
| POST | `/match/quick` | Match rápido sem filtros |
| POST | `/resume/analyze-text` | Analisa texto do currículo |
| POST | `/resume/upload` | Upload de PDF |
| POST | `/resume/analyze-and-match` | Analisa currículo + ranqueia vagas |

Documentação completa: `http://localhost:8000/docs`

---

## 🛠️ Tech Stack

| Camada | Tecnologia |
|--------|------------|
| API | Python, FastAPI, Pydantic |
| NLP | spaCy, regex, dicionário customizado |
| Scoring | Jaccard Similarity, algoritmo próprio |
| Interface | Streamlit |
| Dados | JSON (mock), Gupy API (em breve) |

---

## 📈 Roadmap

- [x] Motor de scoring com 5 dimensões
- [x] Extrator de skills com NLP
- [x] API REST com FastAPI
- [x] Interface visual com Streamlit
- [ ] Upload de PDF direto
- [ ] Integração com API de vagas reais (Gupy, Adzuna)
- [ ] Deploy em cloud (AWS EC2)
- [ ] Dashboard de evolução de perfil
- [ ] Reescrita de currículo por vaga

---

## 👨‍💻 Autor

**Arthur Giribola**
- LinkedIn: [linkedin.com/in/arthurgiribola](https://linkedin.com/in/arthurgiribola)
- GitHub: [github.com/ArthurGiribola](https://github.com/ArthurGiribola)

---

## 📄 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.