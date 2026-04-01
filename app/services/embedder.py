"""
Embedder — AI Job Matcher
Converte texto em vetores semânticos usando sentence-transformers.
Modelo: all-MiniLM-L6-v2 (80MB, rápido, qualidade suficiente para matching técnico)
"""

from sentence_transformers import SentenceTransformer
import numpy as np

# Carrega o modelo uma vez — fica em memória durante a sessão
# Na primeira execução baixa ~80MB automaticamente
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model() -> SentenceTransformer:
    """
    Retorna o modelo carregado.
    Lazy loading — só carrega quando chamado pela primeira vez.
    """
    global _model
    if _model is None:
        print(f"Carregando modelo {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
        print("Modelo carregado.")
    return _model


def embed_text(text: str) -> np.ndarray:
    """
    Converte um texto em vetor de embeddings.
    Retorna array numpy de shape (384,).
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def embed_resume(resume_text: str) -> np.ndarray:
    """
    Gera embedding do currículo.
    Limita a 512 tokens — o modelo não processa mais que isso.
    """
    truncated = resume_text[:3000]
    return embed_text(truncated)


def embed_job(job: dict) -> np.ndarray:
    """
    Gera embedding de uma vaga.
    Combina título + descrição + skills para contexto máximo.
    """
    title = job.get("title", "")
    description = job.get("description", "")
    skills = ", ".join(job.get("skills_required", []))

    combined = f"{title}. {description}. Required skills: {skills}"
    truncated = combined[:3000]
    return embed_text(truncated)
def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calcula cosine similarity entre dois vetores.
    Retorna valor entre -1 e 1. Para textos, sempre entre 0 e 1.
    1.0 = idênticos, 0.0 = sem relação semântica.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calcula similaridade semântica entre dois textos.
    Retorna score entre 0.0 e 1.0.
    """
    vec_a = embed_text(text_a)
    vec_b = embed_text(text_b)
    return cosine_similarity(vec_a, vec_b)


def resume_job_similarity(resume_text: str, job: dict) -> float:
    """
    Calcula similaridade semântica entre currículo e vaga.
    Retorna score entre 0.0 e 1.0.
    """
    vec_resume = embed_resume(resume_text)
    vec_job = embed_job(job)
    return cosine_similarity(vec_resume, vec_job)