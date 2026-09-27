import re
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Job, Skill, User, UserSkill

SKILL_CATALOG = {
    "Python": "Programming", "Java": "Programming", "C++": "Programming", "SQL": "Database",
    "Machine Learning": "AI/ML", "Deep Learning": "AI/ML", "NLP": "AI/ML", "Generative AI": "AI/ML",
    "RAG": "AI/ML", "Docker": "DevOps", "AWS": "Cloud", "Git": "Tools", "React": "Web Development",
    "FastAPI": "Web Development", "PostgreSQL": "Database", "Statistics": "Data Science", "Pandas": "Data Science",
}

ROLE_SKILLS = {
    "AI Engineer": ["Python", "Machine Learning", "Deep Learning", "NLP", "RAG", "Docker", "AWS", "SQL"],
    "ML Engineer": ["Python", "Machine Learning", "Deep Learning", "Docker", "AWS", "SQL"],
    "Data Scientist": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas"],
    "Backend Developer": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
    "Full Stack Developer": ["React", "Python", "FastAPI", "PostgreSQL", "Git"],
}

DEMO_JOBS = [
    {"title": "AI Engineer Intern", "company": "Northstar Labs (Demo)", "location": "Remote", "employment_type": "Internship", "required_skills": ["Python", "Machine Learning", "RAG", "Docker"], "preferred_skills": ["FastAPI", "AWS"], "description": "Build retrieval-enabled AI features with an engineering team. This is clearly labelled CareerOS demo data."},
    {"title": "Junior Data Scientist", "company": "SignalWorks (Demo)", "location": "Bengaluru", "employment_type": "Full-time", "required_skills": ["Python", "SQL", "Statistics", "Machine Learning"], "preferred_skills": ["Pandas", "NLP"], "description": "Explore datasets, create models, and communicate analyses. This is clearly labelled CareerOS demo data."},
    {"title": "Backend Engineer Intern", "company": "Platformly (Demo)", "location": "Remote", "employment_type": "Internship", "required_skills": ["Python", "FastAPI", "PostgreSQL", "Git"], "preferred_skills": ["Docker", "AWS"], "description": "Ship secure API endpoints and data integrations. This is clearly labelled CareerOS demo data."},
]

def seed_catalog(db: Session):
    if not db.scalar(select(Skill.id).limit(1)):
        db.add_all([Skill(name=name, category=category) for name, category in SKILL_CATALOG.items()])
    if not db.scalar(select(Job.id).limit(1)):
        db.add_all([Job(**job) for job in DEMO_JOBS])
    db.commit()

def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    return [skill for skill in SKILL_CATALOG if re.search(r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)", lower)]

def user_skill_names(db: Session, user_id: int) -> list[str]:
    return list(db.scalars(select(Skill.name).join(UserSkill).where(UserSkill.user_id == user_id)).all())

def job_match(user_skills: list[str], job: Job) -> dict:
    owned = {item.lower() for item in user_skills}
    required = job.required_skills or []
    preferred = job.preferred_skills or []
    matched = [skill for skill in required + preferred if skill.lower() in owned]
    missing = [skill for skill in required if skill.lower() not in owned]
    skill_similarity = len([s for s in required if s.lower() in owned]) / max(len(required), 1)
    preferred_similarity = len([s for s in preferred if s.lower() in owned]) / max(len(preferred), 1)
    # Demo-safe transparent compatibility heuristic: not a hiring prediction.
    score = round(min(100, 25 + 60 * skill_similarity + 15 * preferred_similarity))
    return {"match_score": score, "matched_skills": matched, "missing_skills": missing,
            "explanation": f"Compatibility is based on {len(matched)} demonstrated skills; it is not a hiring probability."}

def roadmap_for(role: str, months: int, hours: int, user_skills: list[str]) -> list[dict]:
    targets = ROLE_SKILLS.get(role, ROLE_SKILLS["AI Engineer"])
    missing = [skill for skill in targets if skill not in user_skills] or targets[:3]
    return [{"skill": skill, "title": f"Build practical {skill} fluency", "description": f"Learn {skill} through focused study and one portfolio-quality exercise.", "resources": ["Curated resource links are added through the knowledge base; verify provider details before relying on them."], "priority": "High" if i < 3 else "Medium", "estimated_hours": max(6, (months * hours * 4) // len(missing)), "status": "todo"} for i, skill in enumerate(missing)]
