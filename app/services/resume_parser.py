"""
Resume Parser — AI Job Matcher
Extrai texto de PDFs e identifica skills automaticamente.
"""

import re
from pathlib import Path
from pdfminer.high_level import extract_text

# Dicionário de skills reconhecidas pelo sistema
SKILLS_DICT = {
    # Linguagens
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "php", "ruby", "scala", "r",
    # Web
    "react", "vue", "angular", "html", "css", "node.js", "fastapi", "django",
    "flask", "express", "next.js",
    # Dados & ML
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "machine learning", "deep learning", "nlp", "computer vision",
    "neural networks", "mlflow", "huggingface",
    # Banco de dados
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "oracle", "sql",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd",
    "github actions", "linux", "nginx",
    # Ferramentas
    "git", "github", "jira", "figma", "power bi", "tableau",
    # Outros
    "rest api", "graphql", "microservices", "spark", "airflow", "kafka",
    "statistics", "probability", "linear algebra", "langchain",
    "vector databases", "llm",
}

# Mapeamento de variações para nome padrão
SKILL_ALIASES = {
    "sklearn": "scikit-learn",
    "sci-kit learn": "scikit-learn",
    "node": "node.js",
    "nodejs": "node.js",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "machine learning",
    "ec2": "aws",
    "s3": "aws",
    "lambda": "aws",
}

# Palavras que indicam senioridade
SENIORITY_KEYWORDS = {
    "junior": ["junior", "jr", "entry level", "entry-level", "iniciante", "estágio", "estagio", "intern", "trainee"],
    "mid": ["pleno", "mid", "mid-level", "intermediário", "intermediario", "2 anos", "3 anos", "4 anos"],
    "senior": ["senior", "sênior", "sr", "especialista", "specialist", "5 anos", "6 anos", "7 anos", "8 anos"],
    "lead": ["lead", "líder", "lider", "tech lead", "principal", "staff", "architect", "arquiteto"],
}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrai texto bruto de um arquivo PDF."""
    try:
        text = extract_text(pdf_path)
        return text or ""
    except Exception as e:
        return ""


def clean_text(text: str) -> str:
    """Limpa o texto removendo caracteres especiais e espaços extras."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\+\#\/\-]', ' ', text)
    return text.strip().lower()


def extract_skills(text: str) -> list[str]:
    """
    Extrai skills do texto usando dicionário + aliases.
    Retorna lista de skills únicas normalizadas.
    """
    text_lower = text.lower()
    found_skills = set()

    # Verifica aliases primeiro
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            found_skills.add(canonical)

    # Verifica dicionário principal
    for skill in SKILLS_DICT:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill)

    # Capitaliza corretamente para exibição
    display_map = {
        "python": "Python", "java": "Java", "javascript": "JavaScript",
        "typescript": "TypeScript", "c++": "C++", "c#": "C#",
        "go": "Go", "rust": "Rust", "kotlin": "Kotlin", "swift": "Swift",
        "php": "PHP", "ruby": "Ruby", "scala": "Scala",
        "react": "React", "vue": "Vue", "angular": "Angular",
        "html": "HTML", "css": "CSS", "node.js": "Node.js",
        "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
        "pandas": "pandas", "numpy": "NumPy", "scikit-learn": "scikit-learn",
        "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
        "machine learning": "Machine Learning", "deep learning": "Deep Learning",
        "nlp": "NLP", "computer vision": "Computer Vision",
        "neural networks": "Neural Networks", "mlflow": "MLflow",
        "huggingface": "HuggingFace", "postgresql": "PostgreSQL",
        "mysql": "MySQL", "mongodb": "MongoDB", "redis": "Redis",
        "sqlite": "SQLite", "oracle": "Oracle", "sql": "SQL",
        "aws": "AWS", "gcp": "GCP", "azure": "Azure",
        "docker": "Docker", "kubernetes": "Kubernetes",
        "terraform": "Terraform", "ci/cd": "CI/CD",
        "git": "Git", "github": "GitHub", "linux": "Linux",
        "rest api": "REST API", "graphql": "GraphQL",
        "microservices": "Microservices", "spark": "Spark",
        "airflow": "Airflow", "kafka": "Kafka",
        "statistics": "Statistics", "probability": "Probability",
        "linear algebra": "Linear Algebra", "langchain": "LangChain",
        "vector databases": "Vector Databases", "llm": "LLM",
        "power bi": "Power BI", "tableau": "Tableau",
        "r": "R", "figma": "Figma", "jira": "Jira",
        "github actions": "GitHub Actions", "nginx": "Nginx",
        "next.js": "Next.js", "express": "Express",
    }

    return sorted([display_map.get(s, s.title()) for s in found_skills])


def detect_seniority(text: str) -> str:
    """
    Detecta o nível de senioridade com base em palavras-chave.
    Retorna: junior | mid | senior | lead
    """
    text_lower = text.lower()
    scores = {"junior": 0, "mid": 0, "senior": 0, "lead": 0}

    for level, keywords in SENIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[level] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "junior"


def extract_sections(text: str) -> dict:
    """
    Divide o texto do currículo em seções principais.
    """
    sections = {
        "experience": "",
        "education": "",
        "skills": "",
        "summary": "",
        "projects": "",
    }

    section_patterns = {
        "experience": r"(experience|experiência|trabalho|work|emprego)",
        "education": r"(education|educação|formação|academic|graduação)",
        "skills": r"(skills|habilidades|tecnologias|stack|competências)",
        "summary": r"(summary|resumo|about|sobre|objetivo|profile)",
        "projects": r"(projects|projetos|portfolio)",
    }

    lines = text.split('\n')
    current_section = "summary"

    for line in lines:
        line_lower = line.lower().strip()
        matched = False
        for section, pattern in section_patterns.items():
            if re.search(pattern, line_lower) and len(line_lower) < 50:
                current_section = section
                matched = True
                break
        if not matched:
            sections[current_section] += line + "\n"

    return sections


def parse_resume_text(text: str) -> dict:
    """
    Processa texto do currículo e retorna perfil estruturado.
    Entrada: texto bruto do currículo
    Saída: dict com skills, senioridade, seções e resumo
    """
    cleaned = clean_text(text)
    skills = extract_skills(cleaned)
    seniority = detect_seniority(cleaned)
    sections = extract_sections(text)

    # Skills de alto valor que o candidato tem
    high_value = {"AWS", "GCP", "Azure", "Machine Learning", "Docker",
                  "Kubernetes", "LLM", "LangChain", "MLflow", "HuggingFace"}
    strengths = [s for s in skills if s in high_value]

    return {
        "skills": skills,
        "total_skills": len(skills),
        "seniority": seniority,
        "strengths": strengths,
        "sections": {k: v.strip() for k, v in sections.items() if v.strip()},
        "raw_text_length": len(text),
    }


def parse_resume_pdf(pdf_path: str) -> dict:
    """
    Processa um arquivo PDF e retorna perfil estruturado.
    Entrada: caminho para o arquivo PDF
    Saída: mesmo formato do parse_resume_text
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {"error": "Não foi possível extrair texto do PDF."}
    result = parse_resume_text(text)
    result["source"] = "pdf"
    result["filename"] = Path(pdf_path).name
    return result