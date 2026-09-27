from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    location: str | None = None
    college: str | None = None
    degree: str | None = None
    branch: str | None = None
    graduation_year: int | None = None
    target_role: str | None = None
    target_industry: str | None = None
    career_goal: str | None = None

class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    proficiency: int = Field(ge=0, le=100, default=50)
    years_experience: float = Field(ge=0, le=60, default=0)

class RoadmapRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    duration_months: int = Field(ge=1, le=12, default=3)
    hours_per_week: int = Field(ge=1, le=60, default=8)

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=8000)
