"""Constrained demo orchestrator; agents receive only derived profile context."""
from ..services.career import ROLE_SKILLS

def respond(message: str, profile: dict, skills: list[str]) -> dict:
    message_lower = message.lower()
    role = profile.get("target_role") or "AI Engineer"
    targets = ROLE_SKILLS.get(role, ROLE_SKILLS["AI Engineer"])
    gaps = [skill for skill in targets if skill not in skills]
    if any(word in message_lower for word in ["gap", "learn", "roadmap"]):
        answer = f"For {role}, your highest-value next skills are {', '.join(gaps[:3]) or 'portfolio depth and interview practice'}. Start with one project that demonstrates them together."
        agent = "Learning Agent"
    elif "interview" in message_lower:
        answer = "Practice concise STAR stories for projects, then explain one technical decision, trade-off, and result. I can generate role-specific questions in the Interview workspace."
        agent = "Interview Agent"
    elif "resume" in message_lower:
        answer = "Use achievement-oriented bullets: action, technical method, and observable result. Only include claims you can discuss confidently in an interview."
        agent = "Resume Agent"
    else:
        answer = f"Your profile is being considered for {role}. The next practical step is to strengthen {', '.join(gaps[:2]) or 'evidence of your current skills'} with a scoped project and reflect it in your resume."
        agent = "Career Agent"
    return {"agent": agent, "answer": answer, "grounding": "Demo-mode response grounded in your saved profile and CareerOS role-skill catalog. Recommendations are not hiring guarantees."}
