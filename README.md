# 🎯 AI Job Matcher

> Plataforma inteligente de matching de vagas com análise de currículo por IA, coaching de carreira personalizado e ferramentas profissionais powered by Claude AI.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-red)
![Claude AI](https://img.shields.io/badge/Claude-Haiku-orange)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green)
![Deploy](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-brightgreen)

## 🔗 Demo ao vivo
**[ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app](https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app)**

---

## ✨ Features

### 🤖 Análise de Currículo com IA
- Extração estruturada de skills, nível de senioridade e red flags usando **Claude Haiku**
- Validação de qualidade do currículo com score 0-100
- Embeddings semânticos com **sentence-transformers** para matching preciso

### 💼 Matching de Vagas
- **5 fontes de vagas**: Adzuna, Remotive, Reed, Jooble, The Muse
- Scoring ponderado: semântico + senioridade + recência + filtros
- Probabilidade de contratação via **Logistic Regression**
- Enriquecimento de vagas com Claude para extração de skills reais
- Detector de red flags nas vagas

### 📝 Ferramentas de Carreira
- **Cover Letter** personalizado por vaga
- **Sugestões de melhoria** do currículo por vaga
- **Geração de currículo profissional** completo
- **Tradução para inglês** profissional e ATS-friendly
- **Score de mercado** com faixas salariais em R$, £ e $
- **Comparador de vagas** lado a lado

### 📊 Histórico e Persistência
- Botão "Apliquei para essa vaga" com histórico na sidebar
- Persistência via **Supabase** (PostgreSQL)
- Cache de vagas com TTL de 1 hora

---

## 🛠️ Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Streamlit |
| AI/LLM | Anthropic Claude Haiku |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| ML | scikit-learn (Logistic Regression) |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL) |
| Deploy | Streamlit Cloud |
| Vagas | Adzuna, Remotive, Reed, Jooble, The Muse |

---

## 🚀 Como rodar localmente

### 1. Clone o repositório
```bash
git clone https://github.com/ArthurGiribola/ai-job-matcher.git
cd ai-job-matcher
```

### 2. Crie o ambiente virtual e instale as dependências
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz:
```env
ANTHROPIC_API_KEY=sua_chave_aqui
ADZUNA_APP_ID=seu_app_id
ADZUNA_APP_KEY=sua_app_key
REED_API_KEY=sua_chave_reed
JOOBLE_API_KEY=sua_chave_jooble
SUPABASE_URL=sua_url_supabase
SUPABASE_ANON_KEY=sua_chave_supabase
```

### 4. Inicie o app
```bash
# Windows — dois cliques no start.bat
# ou
streamlit run frontend/app.py
```

---

## 📁 Estrutura do projeto
```
ai-job-matcher/
├── app/
│   └── services/
│       ├── resume_analyzer.py    # Claude AI — análise, cover letter, sugestões
│       ├── job_collector.py      # 5 fontes de vagas + cache + enriquecimento
│       ├── scoring_engine.py     # Scoring ponderado + embeddings semânticos
│       ├── hiring_predictor.py   # Probabilidade de contratação (ML)
│       ├── embedder.py           # sentence-transformers
│       ├── resume_parser.py      # Extração de texto de PDF
│       └── database.py           # Supabase CRUD
├── frontend/
│   └── app.py                    # Streamlit UI
├── tests/                        # 31 testes
├── data/
│   └── mock_jobs.json            # Fallback de vagas
├── start.bat                     # Inicialização local (Windows)
└── requirements.txt
```

---

## 🧪 Testes

```bash
python -m pytest tests/ -q
# 31 passed
```

---

## 📸 Screenshots

> Em breve

---

## 🗺️ Roadmap

- [ ] Download de currículo em PDF com template profissional
- [ ] Autenticação de usuários
- [ ] Dashboard de progresso de carreira
- [ ] Alertas de novas vagas por email
- [ ] Frontend React

---

## 👨‍💻 Autor

**Arthur Giribola**
- GitHub: [@ArthurGiribola](https://github.com/ArthurGiribola)
- LinkedIn: [linkedin.com/in/arthurgiribola](https://linkedin.com/in/arthurgiribola)

---

## 📄 Licença

MIT License
