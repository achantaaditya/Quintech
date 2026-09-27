from pathlib import Path
import fitz
from docx import Document
from .career import extract_skills

def extract_text(path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf)
    if suffix == ".docx":
        return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    raise ValueError("Only PDF and DOCX files are supported")

def analyze(text: str) -> dict:
    normalized = " ".join(text.split())
    lower = normalized.lower()
    sections = {"contact": any(x in lower for x in ["@", "linkedin", "phone"]), "education": "education" in lower,
                "skills": "skills" in lower, "experience": any(x in lower for x in ["experience", "internship"]),
                "projects": "project" in lower}
    missing = [name.title() for name, found in sections.items() if not found]
    skills = extract_skills(normalized)
    score = min(95, max(30, 45 + len(skills) * 5 + sum(sections.values()) * 5 - len(missing) * 2))
    recommendations = []
    if missing: recommendations.append("Add clearly labelled " + ", ".join(missing[:2]) + " section(s).")
    if len(normalized.split()) < 180: recommendations.append("Add quantified project outcomes and relevant detail where truthful.")
    recommendations.append("Tailor keywords to a specific job description without keyword stuffing.")
    return {"score": score, "skills": skills, "summary": f"Resume contains {len(normalized.split())} words and {len(skills)} recognised catalog skills.",
            "strengths": (["Recognised technical skills"] if skills else []) + (["Core resume sections present"] if len(missing) <= 2 else []),
            "weaknesses": ["Some expected sections are missing"] if missing else ["Review impact statements for specificity"],
            "missing_sections": missing, "keyword_analysis": {"recognised_skills": skills, "word_count": len(normalized.split())}, "recommendations": recommendations}
