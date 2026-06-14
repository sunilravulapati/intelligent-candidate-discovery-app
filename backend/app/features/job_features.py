"""
Feature extraction and calculation utilities for job descriptions.
"""
from typing import Dict, Any, List
from app.models.domain import Job

def extract_job_intent(job: Job) -> Dict[str, Any]:
    """
    Extracts semantic intent, required level of seniority, target industry,
    and key technology categories from the job title and description.
    """
    # Placeholder implementation
    return {
        "title": job.title,
        "seniority_level": "Senior",
        "tech_categories": []
    }

def normalize_required_skills(job: Job) -> List[str]:
    """
    Normalizes the user-specified required skills lists for synonym mapping and standardizations.
    """
    # Placeholder implementation
    return job.required_skills
