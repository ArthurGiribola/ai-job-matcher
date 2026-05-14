# AI Job Matcher

> Plataforma de matching de vagas com análise de currículo por IA, coaching de carreira e ferramentas profissionais — powered by Claude Haiku e sentence-transformers.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-red)
![Claude AI](https://img.shields.io/badge/Claude-Haiku-orange)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green)
![Deploy](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-brightgreen)

## Demo ao vivo

**[ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app](https://ai-job-matcher-fwyk2y7xr5aedyhsckxjuw.streamlit.app)**

---

## Features

### Análise de currículo

- **Análise estruturada com Claude Haiku** — extrai skills com nível de proficiência (beginner / intermediate / advanced / expert), anos de uso e evidências do texto; detecta senioridade, complexidade de projetos, pontos fortes, fraquezas e red flags
- **Validação de qualidade** — score 0–100 com avisos específicos (palavras, seções ausentes, red flags)
- **Parser de PDF** — extração de texto via pdfminer.six com fallback para texto colado

### Matching de vagas

- **Matching semântico** — embeddings com `all-MiniLM-L6-v2` (sentence-transformers); cosine similarity entre currículo e vaga completa (título + descrição + skills); cache em memória por sessão
- **Fallback Jaccard** — keyword matching quando embeddings não estão disponíveis
- **Scoring ponderado**: semântico 40% + senioridade 20% + recência 15% + filtros 15% + bônus skills de alta demanda 10%
- **Probabilidade de contratação** — Logistic Regression treinada em dados sintéticos; features: semantic score, cobertura de skills, gap de senioridade, anos de experiência, presença das 3 skills obrigatórias

### Busca de vagas

- **Adzuna API** — 20+ países com busca por país e cidade
- **Autocomplete de cidade** — sugestões via Adzuna Locations API (ativa com 3+ caracteres, cache por sessão)
- **Enriquecimento de skills com IA** — Claude extrai skills reais da descrição de cada vaga
- **Fallback com vagas mock** — 20 vagas de tecnologia brasileiras para uso sem API

### Filtros

- Seleção de país (20+ países)
- Cidade com autocomplete
- Nível de senioridade multiselect (Intern / Junior / Mid / Senior / Lead)
- Apenas vagas remotas
- Score mínimo (slider)
- Número de resultados (slider)
- Conversão de salários para USD com taxa de câmbio em tempo real (open.er-api.com, cache 1h)

### Ferramentas de carreira

- **Carta de apresentação** — dois estilos: Profissional e Ousada; modo de reescrita com score (0–100), análise de problemas e perspectiva do recrutador
- **Sugestões de melhoria do currículo** — por vaga específica
- **Geração de currículo profissional** — Claude reescreve o currículo completo; versão genérica ou otimizada para uma vaga
- **Tradução para inglês** — formato ATS-friendly para candidaturas internacionais
- **Score de mercado** — faixas salariais em BRL, GBP e USD com skills que mais aumentam o valor
- **Conselho personalizado** — Claude gera explicação de fit para as 3 melhores vagas
- **Detector de red flags em vagas** — identifica alertas na descrição
- **Comparador de vagas** — visualização lado a lado de até N vagas

### Histórico

- Botão "Apliquei para essa vaga" por vaga
- Persistência via Supabase (PostgreSQL); fallback para session_state sem credenciais
- Histórico exibido na sidebar com score e probabilidade de contratação

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Streamlit 1.56 |
| AI / LLM | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 80 MB) |
| ML | scikit-learn — Logistic Regression |
| PDF | pdfminer.six |
| Backend | FastAPI (não usado pelo frontend — standalone) |
| Database | Supabase (PostgreSQL) |
| Jobs API | Adzuna (20+ países) |
| FX API | open.er-api.com |
| Deploy | Streamlit Cloud |

---

## Performance

Benchmarked em `all-MiniLM-L6-v2` rodando em CPU (Windows 11).

| # | Par currículo / vaga | Score de similaridade | Latência |
|---|----------------------|:---------------------:|--------:|
| 1 | Python ML Engineer — match forte | 0.735 | 774 ms |
| 2 | Frontend React Dev — match forte | 0.870 | 38 ms |
| 3 | Backend Python Dev — match parcial (vaga Go) | 0.562 | 37 ms |
| 4 | Analista de Dados — match moderado (vaga Data Scientist) | 0.583 | 36 ms |
| 5 | DevOps Engineer — match forte | 0.836 | 43 ms |
| | **Média** | **0.717** | **186 ms** |

- **Cold start** (carregamento do modelo): ~2.7 s — ocorre uma vez por sessão
- **Latência quente** (pares 2–5): ~38 ms por match
- O par 1 é mais lento (~774 ms) por inicializar o cache do tokenizer no primeiro encode

---

## Estrutura do projeto

```
ai-job-matcher/
├── app/
│   ├── main.py                      # FastAPI — 6 endpoints (não usado pelo frontend)
│   └── services/
│       ├── embedder.py              # sentence-transformers + cosine similarity + cache
│       ├── scoring_engine.py        # Scoring ponderado + matching semântico/Jaccard
│       ├── resume_parser.py         # Extração de texto de PDF + keyword parsing
│       ├── resume_analyzer.py       # Claude Haiku — análise, cover letter, sugestões, tradução, mercado
│       ├── job_collector.py         # Adzuna API + enriquecimento com IA + fallback mock
│       ├── hiring_predictor.py      # Logistic Regression — probabilidade de chamada
│       └── database.py              # Supabase CRUD — histórico de candidaturas
├── frontend/
│   └── app.py                       # Streamlit UI (standalone, não depende do FastAPI)
├── data/
│   └── mock_jobs.json               # 20 vagas tech brasileiras (fallback)
├── tests/
│   ├── test_resume_analyzer.py      # 6 testes — integração com Claude
│   ├── test_scoring.py              # Testes de scoring engine
│   ├── test_embedder.py             # Testes de embedding
│   ├── test_semantic_scoring.py     # Testes de matching semântico
│   └── test_debug.py
├── .streamlit/
│   └── secrets.toml.example         # Template de configuração
├── start.bat                         # Inicialização local (Windows)
└── requirements.txt
```

---

## Como rodar localmente

### 1. Clone o repositório

```bash
git clone https://github.com/ArthurGiribola/ai-job-matcher.git
cd ai-job-matcher
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```env
ANTHROPIC_API_KEY=sk-ant-...
ADZUNA_APP_ID=seu_app_id
ADZUNA_APP_KEY=sua_app_key
SUPABASE_URL=https://xxx.supabase.co        # opcional
SUPABASE_ANON_KEY=sua_chave_supabase        # opcional
```

> Sem `SUPABASE_URL` e `SUPABASE_ANON_KEY` o app funciona normalmente — o histórico de candidaturas fica apenas em memória (session_state).

### 4. Inicie o app

```bash
streamlit run frontend/app.py
# ou no Windows: clique duas vezes em start.bat
```

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|----------|:-----------:|-----------|
| `ANTHROPIC_API_KEY` | Sim | Chave da API Anthropic (Claude Haiku) |
| `ADZUNA_APP_ID` | Sim | App ID da Adzuna (vagas reais) |
| `ADZUNA_APP_KEY` | Sim | App Key da Adzuna |
| `SUPABASE_URL` | Não | URL do projeto Supabase |
| `SUPABASE_ANON_KEY` | Não | Chave anon do Supabase |

No Streamlit Cloud: **Settings > Secrets** — cole o conteúdo do `.env` no formato TOML (veja `.streamlit/secrets.toml.example`).

---

## Testes

```bash
python -m pytest tests/test_resume_analyzer.py -q
# 6 passed
```

Os arquivos `test_scoring.py` e `test_embedder.py` dependem de DLLs nativas bloqueadas pelo Application Control do Windows no ambiente de desenvolvimento — não é um bug do código.

---

## Autor

**Arthur Giribola**
- GitHub: [@ArthurGiribola](https://github.com/ArthurGiribola)
- LinkedIn: [linkedin.com/in/arthurgiribola](https://linkedin.com/in/arthurgiribola)

---

## Licença

MIT License
