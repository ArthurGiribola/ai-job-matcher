import re
from pathlib import Path

from app.models.resume import ResumeSection
from app.services.skill_extractor import extract_skills_from_text


def parse_txt_resume(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8")


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_sections(text: str) -> ResumeSection:
    def extract_block(keywords: list[str]) -> str:
        lines = text.splitlines()
        collected = []
        capture = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            low = stripped.lower()

            if any(k in low for k in keywords):
                capture = True
                continue

            if capture and any(
                marker in low
                for marker in [
                    "experiência", "experience",
                    "educação", "education",
                    "skills", "habilidades",
                    "projetos", "projects",
                    "resumo", "summary"
                ]
            ):
                break

            if capture:
                collected.append(stripped)

        return "\n".join(collected).strip()

    experience_text = extract_block(["experiência", "experience"])
    education_text = extract_block(["educação", "education"])
    skills_text = extract_block(["skills", "habilidades", "competências"])
    summary_text = extract_block(["resumo", "summary", "sobre"])
    projects_text = extract_block(["projetos", "projects"])

    return ResumeSection(
        experience=[line for line in experience_text.split("\n") if line.strip()],
        education=[line for line in education_text.split("\n") if line.strip()],
        skills_raw=skills_text,
        summary=summary_text,
        projects=[line for line in projects_text.split("\n") if line.strip()],
    )


def parse_resume_file(file_path: str) -> dict:
    raw_text = parse_txt_resume(file_path)
    cleaned = clean_text(raw_text)
    sections = split_sections(cleaned)

    # 🔥 EXTRAÇÃO DE SKILLS (PARTE NOVA)
    skills = extract_skills_from_text(cleaned)

    return {
        "raw_text": cleaned,
        "sections": sections,
        "skills": skills
    }