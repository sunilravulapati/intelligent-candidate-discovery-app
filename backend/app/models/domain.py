from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class Skill(BaseModel):
    name: str = Field(..., description="Name of the skill")
    proficiency: str = Field(..., description="Proficiency level: beginner, intermediate, advanced, expert")
    endorsements: int = Field(..., description="Number of endorsements received")
    duration_months: int = Field(..., description="Duration of skill usage in months")

# Alias for request compatibility
Skills = Skill

class Experience(BaseModel):
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    start_date: str = Field(..., description="Employment start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Employment end date (YYYY-MM-DD) or null if current")
    duration_months: int = Field(..., description="Duration of employment in months")
    is_current: bool = Field(..., description="Whether this is the current job")
    industry: str = Field(..., description="Industry of the company")
    company_size: str = Field(..., description="Size of the company (e.g. 1-10, 10001+)")
    description: str = Field(..., description="Role responsibilities and achievements")

class Education(BaseModel):
    institution: str = Field(..., description="University or school name")
    degree: str = Field(..., description="Degree type (e.g. B.E., M.Sc)")
    field_of_study: str = Field(..., description="Field of study")
    start_year: int = Field(..., description="Start year")
    end_year: int = Field(..., description="End year")
    grade: Optional[str] = Field(None, description="GPA / percentage / class")
    tier: str = Field(..., description="Prestige tier of the institution: tier_1, tier_2, tier_3, tier_4, unknown")

class Certification(BaseModel):
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuer organization")
    year: int = Field(..., description="Year of issuance")

class Language(BaseModel):
    language: str = Field(..., description="Language name")
    proficiency: str = Field(..., description="Language proficiency: basic, conversational, professional, native")

class ExpectedSalaryRange(BaseModel):
    min: float = Field(..., description="Minimum expected salary in LPA")
    max: float = Field(..., description="Maximum expected salary in LPA")

class ActivitySignals(BaseModel):
    profile_completeness_score: float = Field(..., description="Completeness of candidate profile (0-100)")
    signup_date: str = Field(..., description="Date of signup on Redrob (YYYY-MM-DD)")
    last_active_date: str = Field(..., description="Date of last activity (YYYY-MM-DD)")
    open_to_work_flag: bool = Field(..., description="Whether the candidate is open to new roles")
    profile_views_received_30d: int = Field(..., description="Profile views in the last 30 days")
    applications_submitted_30d: int = Field(..., description="Number of applications submitted in 30 days")
    recruiter_response_rate: float = Field(..., description="Response rate to recruiters (0-1)")
    avg_response_time_hours: float = Field(..., description="Average response time in hours")
    skill_assessment_scores: Dict[str, float] = Field(..., description="Scores for skill assessments (0-100)")
    connection_count: int = Field(..., description="Connection count on Redrob")
    endorsements_received: int = Field(..., description="Total endorsements received")
    notice_period_days: int = Field(..., description="Stated notice period in days")
    expected_salary_range_inr_lpa: ExpectedSalaryRange = Field(..., description="Expected salary range in LPA")
    preferred_work_mode: str = Field(..., description="Preferred work mode: remote, hybrid, onsite, flexible")
    willing_to_relocate: bool = Field(..., description="Whether candidate is willing to relocate")
    github_activity_score: float = Field(..., description="GitHub contributions score (-1 to 100)")
    search_appearance_30d: int = Field(..., description="Times appeared in recruiter search in 30 days")
    saved_by_recruiters_30d: int = Field(..., description="Times saved by recruiters in 30 days")
    interview_completion_rate: float = Field(..., description="Interview attendance rate (0-1)")
    offer_acceptance_rate: float = Field(..., description="Historical offer acceptance rate (-1 to 1)")
    verified_email: bool = Field(..., description="Whether the email is verified")
    verified_phone: bool = Field(..., description="Whether the phone is verified")
    linkedin_connected: bool = Field(..., description="Whether LinkedIn is connected")

class Profile(BaseModel):
    anonymized_name: str = Field(..., description="Anonymized name")
    headline: str = Field(..., description="Professional headline")
    summary: str = Field(..., description="Professional summary")
    location: str = Field(..., description="Location (City, State/Country)")
    country: str = Field(..., description="Country")
    years_of_experience: float = Field(..., description="Years of professional experience")
    current_title: str = Field(..., description="Current job title")
    current_company: str = Field(..., description="Current company name")
    current_company_size: Optional[str] = Field(None, description="Size of current company")
    current_industry: Optional[str] = Field(None, description="Current industry")

class Candidate(BaseModel):
    candidate_id: str = Field(..., description="Unique candidate identifier (CAND_XXXXXXX)")
    profile: Profile = Field(..., description="Professional profile metadata")
    career_history: List[Experience] = Field(..., description="Employment history")
    education: List[Education] = Field(..., description="Educational history")
    skills: List[Skill] = Field(..., description="Skills and proficiencies")
    certifications: List[Certification] = Field(default_factory=list, description="Certifications")
    languages: List[Language] = Field(default_factory=list, description="Languages spoken")
    redrob_signals: ActivitySignals = Field(..., description="Engagement and activity signals")

class Job(BaseModel):
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    required_skills: List[str] = Field(default_factory=list, description="List of required skills")

class SearchResult(BaseModel):
    candidate_id: str = Field(..., description="Candidate identifier")
    rank: int = Field(..., description="Rank in search results (1-100)")
    score: float = Field(..., description="Search match score")
    reasoning: Optional[str] = Field(None, description="Explanation for match/ranking")

class RankingOutput(BaseModel):
    candidate_id: str = Field(..., description="Candidate identifier")
    rank: int = Field(..., description="Final rank position (1-100)")
    score: float = Field(..., description="Model match score")
    reasoning: Optional[str] = Field(None, description="Explanation for ranking position")
