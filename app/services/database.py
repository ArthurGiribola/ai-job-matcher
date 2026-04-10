"""
Database service — Supabase integration
Persiste histórico de aplicações entre sessões.
"""
import os
import uuid


def _get_supabase_client():
    """Lazy-loading do cliente Supabase."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            try:
                import streamlit as st
                url = url or st.secrets.get("SUPABASE_URL")
                key = key or st.secrets.get("SUPABASE_ANON_KEY")
            except Exception:
                pass
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"[Supabase] Client failed: {e}")
        return None


def get_or_create_session_id() -> str:
    """Retorna session_id persistente via st.session_state."""
    import streamlit as st
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def save_application(job: dict, result: dict) -> bool:
    """Salva uma aplicação no Supabase."""
    try:
        client = _get_supabase_client()
        if not client:
            return False
        session_id = get_or_create_session_id()
        data = {
            "session_id": session_id,
            "job_id": job.get("id", ""),
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
            "score": result.get("score_percent", ""),
            "hiring_prob": f"{int(result.get('hiring_probability', 0) * 100)}%",
            "country": job.get("country", ""),
            "url": job.get("url", ""),
        }
        client.table("applied_jobs").insert(data).execute()
        print(f"[Supabase] Saved: {job.get('title')}")
        return True
    except Exception as e:
        print(f"[Supabase] Save failed: {e}")
        return False


def load_applications() -> list[dict]:
    """Carrega aplicações da sessão atual do Supabase."""
    try:
        client = _get_supabase_client()
        if not client:
            return []
        session_id = get_or_create_session_id()
        response = client.table("applied_jobs")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("applied_at", desc=True)\
            .execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Load failed: {e}")
        return []


def delete_application(job_id: str) -> bool:
    """Remove uma aplicação do Supabase."""
    try:
        client = _get_supabase_client()
        if not client:
            return False
        session_id = get_or_create_session_id()
        client.table("applied_jobs")\
            .delete()\
            .eq("session_id", session_id)\
            .eq("job_id", job_id)\
            .execute()
        return True
    except Exception as e:
        print(f"[Supabase] Delete failed: {e}")
        return False
