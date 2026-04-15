"""
Embedder — AI Job Matcher
Converte texto em vetores semânticos usando sentence-transformers.
Modelo: all-MiniLM-L6-v2 (80MB, rápido, qualidade suficiente para matching técnico)
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import json
from pathlib import Path

# Carrega o modelo uma vez — fica em memória durante a sessão
# Na primeira execução baixa ~80MB automaticamente
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

# Cache de embeddings de vagas: {cache_key: np.ndarray}
# cache_key = "{job_id}::{job_title}"
_job_embedding_cache: dict[str, np.ndarray] = {}


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
    Resultado cacheado em memória por job_id + title.
    """
    cache_key = f"{job.get('id', '')}::{job.get('title', '')}"
    if cache_key in _job_embedding_cache:
        return _job_embedding_cache[cache_key]

    title = job.get("title", "")
    description = job.get("description", "")
    skills = ", ".join(job.get("skills_required", []))

    combined = f"{title}. {description}. Required skills: {skills}"
    truncated = combined[:3000]
    vec = embed_text(truncated)
    _job_embedding_cache[cache_key] = vec
    return vec


def warmup_mock_jobs() -> None:
    """
    Pré-computa embeddings das vagas mock no startup.
    Evita recalcular em toda requisição durante desenvolvimento.
    """
    mock_path = Path(__file__).parent.parent.parent / "data" / "mock_jobs.json"
    if not mock_path.exists():
        return
    try:
        with open(mock_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        get_model()  # garante que o modelo está carregado antes do loop
        cached = 0
        for job in jobs:
            cache_key = f"{job.get('id', '')}::{job.get('title', '')}"
            if cache_key not in _job_embedding_cache:
                embed_job(job)
                cached += 1
        if cached:
            print(f"[Embedder] Warmup: {cached} mock job embeddings pré-computados.")
    except Exception as e:
        print(f"[Embedder] Warmup falhou: {e}")
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


def resume_job_similarity(resume_text: str, job: dict) -> float:
    """
    Calcula similaridade semântica entre currículo e vaga.
    Retorna score entre 0.0 e 1.0.
    """
    vec_resume = embed_resume(resume_text)
    vec_job = embed_job(job)
    return cosine_similarity(vec_resume, vec_job)