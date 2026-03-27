from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jobs import router as jobs_router
from app.api.match import router as match_router
from app.api.resume import router as resume_router
from app.services.skill_extractor import extract_skills_from_text

app = FastAPI(
    title="AI Job Matcher",
    description="API que analisa currículos e ranqueia vagas por compatibilidade",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(match_router)
app.include_router(resume_router)

@app.get("/")
def root():
    return {"status": "online", "message": "AI Job Matcher rodando!"}


@app.get("/health")
def health():
    return {"status": "ok"}