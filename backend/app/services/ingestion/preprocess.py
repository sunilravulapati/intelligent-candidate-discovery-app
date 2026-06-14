import re
import logging
from typing import Dict, Any, List
from app.models.domain import Candidate, Skill

logger = logging.getLogger(__name__)

# Standard mapping for common skill normalization (synonyms)
SKILL_SYNONYMS = {
    "react.js": "React",
    "reactjs": "React",
    "react native": "React Native",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "ts": "TypeScript",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "fastapi": "FastAPI",
    "aws": "AWS",
    "gcp": "GCP",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "llm": "LLMs",
    "llms": "LLMs",
    "fine-tuning llms": "Fine-tuning LLMs",
    "fine tuning llms": "Fine-tuning LLMs",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes"
}

def clean_text(text: Optional[str]) -> str:
    """Normalizes whitespace, removes trailing/leading spaces, and handles nulls."""
    if not text:
        return ""
    # Remove excessive spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_skill_name(skill_name: str) -> str:
    """Standardizes skill name by stripping, mapping synonyms, and proper casing."""
    cleaned = clean_text(skill_name).lower()
    if cleaned in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[cleaned]
    # Otherwise return title-cased clean name
    return skill_name.strip()

def preprocess_candidate(cand: Candidate) -> Candidate:
    """
    Applies preprocessing to a Candidate model:
    1. Normalizes text fields in candidate profile (headline, summary, location).
    2. Standardizes skill names in candidate skills list.
    3. Standardizes company names in career history.
    
    Returns:
        The preprocessed Candidate object.
    """
    # 1. Clean profile text
    cand.profile.headline = clean_text(cand.profile.headline)
    cand.profile.summary = clean_text(cand.profile.summary)
    cand.profile.location = clean_text(cand.profile.location)
    cand.profile.current_title = clean_text(cand.profile.current_title)
    cand.profile.current_company = clean_text(cand.profile.current_company)
    
    # 2. Normalize and standardize skills
    for skill in cand.skills:
        skill.name = normalize_skill_name(skill.name)
        
    # 3. Standardize career history company and title names
    for job in cand.career_history:
        job.company = clean_text(job.company)
        job.title = clean_text(job.title)
        job.description = clean_text(job.description)
        
    return cand
