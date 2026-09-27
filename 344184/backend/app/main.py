from datetime import datetime
from pathlib import Path
import shutil
import uuid
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .agents.orchestrator import respond
from .config import settings
from .database import Base, engine, get_db
from .models import Interview, InterviewAnswer, InterviewQuestion, Job, Resume, ResumeAnalysis, Roadmap, RoadmapItem, Skill, User, UserProfile, UserSkill
from .schemas import AssistantRequest, InterviewAnswerRequest, LoginRequest, ProfileUpdate, RegisterRequest, RoadmapRequest, SkillInput
from .security import create_token, current_user, hash_password, verify_password
from .services.career import ROLE_SKILLS, extract_skills, job_match, roadmap_for, seed_catalog, user_skill_names
from .services.resume import analyze, extract_text

app = FastAPI(title="CareerOS API", version="0.1.0", description="Career intelligence API; demo scores are advisory, not hiring decisions.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(HTTPException)
async def known_error(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": {"code": "REQUEST_FAILED", "message": str(exc.detail)}})

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    with next(get_db()) as db: seed_catalog(db)

@app.get("/health")
def health(): return {"status": "healthy", "service": "careeros-api", "demo_mode": settings.demo_mode}

@app.get("/ready")
def ready(): return {"status": "ready"}

@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=payload.name, email=payload.email.lower(), password_hash=hash_password(payload.password), profile=UserProfile())
    db.add(user); db.commit(); db.refresh(user)
    return {"success": True, "data": {"user": user_out(user), "access_token": create_token(user.id), "refresh_token": create_token(user.id, True)}}

@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return {"success": True, "data": {"user": user_out(user), "access_token": create_token(user.id), "refresh_token": create_token(user.id, True)}}

@app.post("/api/auth/logout")
def logout(): return {"success": True, "data": {"message": "Logged out. Clear the client token."}}

def user_out(user: User):
    return {"id": user.id, "name": user.name, "email": user.email, "profile": profile_out(user.profile)}

def profile_out(profile: UserProfile | None):
    if not profile: return None
    return {key: getattr(profile, key) for key in ["location", "college", "degree", "branch", "graduation_year", "experience_level", "target_role", "target_industry", "career_goal"]}

@app.get("/api/users/me")
def me(user: User = Depends(current_user)): return {"success": True, "data": user_out(user)}

@app.put("/api/users/me")
def update_profile(payload: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = user.profile or UserProfile(user_id=user.id)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(profile, key, value)
    db.add(profile); db.commit(); db.refresh(profile)
    return {"success": True, "data": profile_out(profile)}

@app.delete("/api/users/me")
def delete_data(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(user); db.commit()
    return {"success": True, "data": {"message": "Your CareerOS data has been deleted."}}

@app.get("/api/skills")
def skills(db: Session = Depends(get_db)):
    return {"success": True, "data": [{"id": s.id, "name": s.name, "category": s.category} for s in db.scalars(select(Skill).order_by(Skill.name))]}

@app.get("/api/users/me/skills")
def my_skills(user: User = Depends(current_user), db: Session = Depends(get_db)):
    records = db.scalars(select(UserSkill).where(UserSkill.user_id == user.id)).all()
    return {"success": True, "data": [{"id": x.id, "name": x.skill.name, "proficiency": x.proficiency, "years_experience": x.years_experience, "source": x.source} for x in records]}

@app.post("/api/users/me/skills")
def add_skill(payload: SkillInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skill = db.scalar(select(Skill).where(Skill.name.ilike(payload.name.strip())))
    if not skill:
        skill = Skill(name=payload.name.strip(), category="Tools"); db.add(skill); db.flush()
    record = db.scalar(select(UserSkill).where(UserSkill.user_id == user.id, UserSkill.skill_id == skill.id))
    if not record: record = UserSkill(user_id=user.id, skill_id=skill.id)
    record.proficiency, record.years_experience = payload.proficiency, payload.years_experience
    db.add(record); db.commit()
    return {"success": True, "data": {"name": skill.name, "proficiency": record.proficiency}}

@app.get("/api/skills/gaps")
def skill_gaps(user: User = Depends(current_user), db: Session = Depends(get_db)):
    names = user_skill_names(db, user.id); role = (user.profile.target_role if user.profile else None) or "AI Engineer"
    target = ROLE_SKILLS.get(role, ROLE_SKILLS["AI Engineer"])
    gaps = [{"skill": s, "priority": "High" if i < 3 else "Medium", "reason": f"Core skill for {role}"} for i, s in enumerate(target) if s not in names]
    return {"success": True, "data": {"target_role": role, "current_skills": names, "target_skills": target, "gaps": gaps}}

@app.post("/api/resumes/upload", status_code=201)
def upload_resume(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}: raise HTTPException(415, "Please upload a PDF or DOCX resume")
    content = file.file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, f"File must be smaller than {settings.max_upload_mb} MB")
    safe_name = f"{uuid.uuid4()}{suffix}"; location = Path(settings.upload_dir) / safe_name
    location.write_bytes(content)
    try: text = extract_text(location, suffix)
    except Exception as exc:
        location.unlink(missing_ok=True); raise HTTPException(422, f"Unable to read this document: {exc}")
    resume = Resume(user_id=user.id, file_name=file.filename or safe_name, file_url=str(location), file_type=suffix[1:], extracted_text=text, processing_status="processed")
    db.add(resume); db.commit(); db.refresh(resume)
    return {"success": True, "data": resume_out(resume)}

def resume_out(resume: Resume):
    return {"id": resume.id, "file_name": resume.file_name, "file_type": resume.file_type, "ats_score": resume.ats_score, "processing_status": resume.processing_status, "uploaded_at": resume.created_at}

@app.get("/api/resumes")
def resumes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": [resume_out(r) for r in db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc()))]}

@app.post("/api/resumes/{resume_id}/analyze")
def analyze_resume(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    if not resume: raise HTTPException(404, "Resume not found")
    result = analyze(resume.extracted_text); resume.ats_score = result["score"]
    if resume.analysis: db.delete(resume.analysis); db.flush()
    db.add(ResumeAnalysis(resume_id=resume.id, **{k: result[k] for k in ["summary", "strengths", "weaknesses", "missing_sections", "keyword_analysis", "recommendations"]}))
    for name in result["skills"]:
        skill = db.scalar(select(Skill).where(Skill.name == name)); exists = db.scalar(select(UserSkill).where(UserSkill.user_id == user.id, UserSkill.skill_id == skill.id))
        if not exists: db.add(UserSkill(user_id=user.id, skill_id=skill.id, source="resume", confidence_score=.85, proficiency=55))
    db.commit()
    return {"success": True, "data": result}

@app.get("/api/jobs")
def jobs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    names = user_skill_names(db, user.id)
    return {"success": True, "data": [{"id": j.id, "title": j.title, "company": j.company, "location": j.location, "employment_type": j.employment_type, "required_skills": j.required_skills, **job_match(names, j), "source": j.source} for j in db.scalars(select(Job).order_by(Job.created_at.desc()))]}

@app.get("/api/jobs/{job_id}")
def job_detail(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    return {"success": True, "data": {"id": job.id, "title": job.title, "company": job.company, "description": job.description, "location": job.location, "required_skills": job.required_skills, "preferred_skills": job.preferred_skills, **job_match(user_skill_names(db, user.id), job)}}

@app.post("/api/roadmap/generate", status_code=201)
def create_roadmap(payload: RoadmapRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = roadmap_for(payload.target_role, payload.duration_months, payload.hours_per_week, user_skill_names(db, user.id))
    roadmap = Roadmap(user_id=user.id, target_role=payload.target_role, duration=f"{payload.duration_months} months", roadmap_data={"hours_per_week": payload.hours_per_week})
    db.add(roadmap); db.flush(); db.add_all([RoadmapItem(roadmap_id=roadmap.id, **item) for item in items]); db.commit(); db.refresh(roadmap)
    return {"success": True, "data": roadmap_out(roadmap)}

def roadmap_out(roadmap: Roadmap):
    return {"id": roadmap.id, "target_role": roadmap.target_role, "duration": roadmap.duration, "items": [{"id": i.id, "skill": i.skill, "title": i.title, "description": i.description, "priority": i.priority, "estimated_hours": i.estimated_hours, "status": i.status} for i in roadmap.items]}

@app.get("/api/roadmap")
def get_roadmap(user: User = Depends(current_user), db: Session = Depends(get_db)):
    roadmap = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc()))
    return {"success": True, "data": roadmap_out(roadmap) if roadmap else None}

@app.put("/api/roadmap/items/{item_id}")
def update_roadmap_item(item_id: int, status: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(RoadmapItem).join(Roadmap).where(RoadmapItem.id == item_id, Roadmap.user_id == user.id))
    if not item: raise HTTPException(404, "Roadmap item not found")
    if status not in {"todo", "in_progress", "complete"}: raise HTTPException(422, "Status must be todo, in_progress, or complete")
    item.status = status; db.commit(); return {"success": True, "data": {"id": item.id, "status": item.status}}

@app.post("/api/assistant/chat")
def assistant(payload: AssistantRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_out(user.profile) or {}; answer = respond(payload.message, profile, user_skill_names(db, user.id))
    return {"success": True, "data": answer}

QUESTIONS = {"AI/ML": ["Explain overfitting and two ways you would mitigate it.", "How would you evaluate a retrieval-augmented generation system?", "Describe a machine learning project from data preparation to deployment."], "Technical": ["Describe a technical challenge in a project and how you resolved it.", "How would you design a secure API endpoint?", "What trade-offs would you consider when choosing a database?"], "HR": ["Tell me about a time you learned something difficult.", "Why are you interested in this role?", "Describe how you handle feedback."]}

@app.post("/api/interviews", status_code=201)
def start_interview(interview_type: str = "Technical", difficulty: str = "Intermediate", user: User = Depends(current_user), db: Session = Depends(get_db)):
    role = (user.profile.target_role if user.profile else None) or "AI Engineer"; prompts = QUESTIONS.get(interview_type, QUESTIONS["Technical"])
    interview = Interview(user_id=user.id, interview_type=interview_type, target_role=role, difficulty=difficulty)
    db.add(interview); db.flush(); db.add_all([InterviewQuestion(interview_id=interview.id, question=q, category=interview_type, difficulty=difficulty, expected_topics=[]) for q in prompts]); db.commit(); db.refresh(interview)
    return {"success": True, "data": interview_out(interview)}

def interview_out(interview: Interview):
    return {"id": interview.id, "interview_type": interview.interview_type, "target_role": interview.target_role, "difficulty": interview.difficulty, "overall_score": interview.overall_score, "questions": [{"id": q.id, "question": q.question, "answer": q.answer.answer if q.answer else None, "score": q.answer.score if q.answer else None} for q in interview.questions]}

@app.post("/api/interviews/{interview_id}/answer")
def answer_interview(interview_id: int, question_id: int, payload: InterviewAnswerRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    question = db.scalar(select(InterviewQuestion).join(Interview).where(InterviewQuestion.id == question_id, InterviewQuestion.interview_id == interview_id, Interview.user_id == user.id))
    if not question: raise HTTPException(404, "Interview question not found")
    words = len(payload.answer.split()); score = min(95, max(35, 45 + min(words, 180) // 4))
    if question.answer: db.delete(question.answer); db.flush()
    db.add(InterviewAnswer(question_id=question.id, answer=payload.answer, score=score, feedback="Demo evaluation considers answer length and prompts structured reflection; it does not assess employability.", strengths=["Provided a complete response"], weaknesses=["Add specific evidence and trade-offs where relevant."]))
    db.commit(); return {"success": True, "data": {"score": score, "feedback": "Demo evaluation considers clarity cues, not a real hiring decision."}}

@app.post("/api/interviews/{interview_id}/complete")
def complete_interview(interview_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    interview = db.scalar(select(Interview).where(Interview.id == interview_id, Interview.user_id == user.id))
    if not interview: raise HTTPException(404, "Interview not found")
    answered = [q.answer.score for q in interview.questions if q.answer]; interview.overall_score = round(sum(answered) / len(answered)) if answered else 0; interview.completed_at = datetime.utcnow(); db.commit()
    return {"success": True, "data": interview_out(interview)}

@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    names = user_skill_names(db, user.id); resumes = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all(); roadmap = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc()))
    jobs = list(db.scalars(select(Job)).all()); recommendations = sorted([{"title": j.title, "company": j.company, **job_match(names, j)} for j in jobs], key=lambda x: x["match_score"], reverse=True)
    complete = sum(i.status == "complete" for i in roadmap.items) if roadmap else 0; total = len(roadmap.items) if roadmap else 0
    resume_score = resumes[0].ats_score if resumes and resumes[0].ats_score else 0; skill_score = min(100, len(names) * 10)
    readiness = round((resume_score * .3 + skill_score * .3 + (recommendations[0]["match_score"] if recommendations else 0) * .2 + (complete / total * 100 if total else 0) * .2))
    return {"success": True, "data": {"readiness_score": readiness, "breakdown": {"resume": resume_score, "skills": skill_score, "projects": 0, "interview": 0, "job_match": recommendations[0]["match_score"] if recommendations else 0}, "top_skills": names[:6], "skill_gaps": [s for s in ROLE_SKILLS.get((user.profile.target_role if user.profile else "") or "AI Engineer", []) if s not in names][:4], "recommended_jobs": recommendations[:3], "roadmap_progress": {"complete": complete, "total": total}, "recommendation": f"Focus next on {(ROLE_SKILLS.get((user.profile.target_role if user.profile else "") or "AI Engineer", []) or ['your target skills'])[0]} and demonstrate it in a project. Demo scores are advisory."}}
