from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    experience: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    skills_raw: str = ""
    summary: str = ""
    projects: list[str] = Field(default_factory=list)


class Resume(BaseModel):
    id: str
    filename: str
    raw_text: str
    sections: ResumeSection
    extracted_skills: list[str] = Field(default_factory=list)