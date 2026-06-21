"""
create_submission.py
====================
Generates the final ranked submission CSV for the Redrob challenge.

Pipeline:
  1. Load JD from job_description.docx (extracted dynamically)
  2. Load all candidates + FAISS index
  3. Retrieve top-500 via FAISS semantic search using a precision-tuned JD query
  4. Apply JD-aware hybrid scoring with disqualifier penalties
  5. Output top-100 sorted by score (non-increasing), tie-break by candidate_id asc
  6. Automatically validate submission format before exiting using validate_submission.py

Run:
    cd backend
    .\\venv\\Scripts\\python scripts/create_submission.py
"""
import sys
import os
import re
import zipfile
import argparse
import logging
import math
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import _match_required_skills, _SKILL_ALIASES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── JD Parsing Helpers ────────────────────────────────────────────────────────

def read_docx(file_path: str) -> str:
    """Extract all text paragraphs from a .docx file using a standard zipfile XML parser."""
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            texts = [elem.text for elem in root.iter() if elem.tag.endswith('}t') and elem.text]
            return "".join(texts)
    except Exception as e:
        logger.error(f"Error reading docx from '{file_path}': {e}")
        return ""

def read_job_description(file_path: str) -> str:
    """Read a job description from a docx or text file."""
    if file_path.lower().endswith(".docx"):
        return read_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

def extract_skills_from_jd(text: str) -> List[str]:
    """Dynamically extract canonical skills from the job description text using our 60+ alias map."""
    text_lower = text.lower()
    extracted = []
    for canonical, aliases in _SKILL_ALIASES.items():
        for alias in aliases:
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                extracted.append(canonical)
                break
    return sorted(list(set(extracted)))


# ── Predefined presets for the Founding AI Engineer role ────────────────────

PRESET_JOB_TITLE = "Senior AI Engineer — Founding Team"

# Precision-tuned semantic query constructed for FAISS embedding retrieval
PRESET_SEMANTIC_QUERY = (
    "Headline: Senior AI Engineer Machine Learning Engineer NLP Engineer. "
    "Current Role: AI Engineer at product company startup. "
    "Summary: Production experience with embeddings retrieval systems sentence-transformers "
    "vector databases FAISS hybrid search ranking systems. "
    "Built end-to-end recommendation search ranking systems deployed to real users at product companies. "
    "Designed evaluation frameworks NDCG MRR MAP for ranking quality. "
    "Strong Python software engineering, not just research or consulting. "
    "Applied ML production deployment 5 to 9 years experience. "
    "Skills: sentence-transformers embeddings FAISS vector search hybrid retrieval BM25 "
    "XGBoost learning-to-rank NDCG MRR evaluation Python NLP information retrieval "
    "recommendation systems machine learning deep learning LLM fine-tuning "
    "Pinecone Weaviate Qdrant Elasticsearch OpenSearch Milvus. "
    "Experience: AI Engineer at startup | ML Engineer at product company | "
    "NLP Engineer | Search Engineer | Ranking Systems | Recommendation Engine."
)

PRESET_REQUIRED_SKILLS = [
    "embeddings",
    "retrieval",
    "vector databases",
    "faiss",
    "python",
    "nlp",
    "machine learning",
    "ranking",
    "recommendation",
    "information retrieval",
    "sentence-transformers",
    "evaluation",
    "ndcg",
    "mrr",
    "map",
    "xgboost",
    "learning to rank",
    "elasticsearch",
    "pinecone",
    "weaviate",
    "qdrant",
    "hybrid search",
]

# AI/ML-adjacent titles that indicate genuine technical fit
POSITIVE_TITLE_KEYWORDS = {
    "ai", "ml", "machine learning", "nlp", "deep learning", "data scientist",
    "research engineer", "applied scientist", "search engineer", "ranking",
    "recommendation", "computer vision", "natural language", "llm",
    "backend engineer", "software engineer", "platform engineer", "data engineer",
    "fullstack", "full stack", "infrastructure engineer",
}

# Titles that are strong disqualifiers (non-technical or non-AI roles)
DISQUALIFIER_TITLE_KEYWORDS = {
    "marketing manager", "hr manager", "operations manager", "sales manager",
    "business analyst", "civil engineer", "mechanical engineer", "electrical engineer",
    "project manager", "product manager", "account manager", "finance",
    "chartered accountant", "supply chain", "logistics", "procurement",
    "teacher", "professor", "lecturer", "doctor", "nurse", "architect",
}

# Companies known to be pure IT services / consulting (disqualifier if entire career)
CONSULTING_COMPANIES = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "tech mahindra", "mphasis", "hexaware", "ltimindtree",
    "l&t infotech", "persistent systems", "mastech", "niit technologies",
}

# Hybrid scoring weights — tuned to the JD priorities
WEIGHTS = {
    "semantic":      0.45,  # FAISS cosine similarity (main discriminator)
    "skill_overlap": 0.20,  # Jaccard overlap with required skills
    "ai_title_fit":  0.15,  # Penalty/bonus based on title relevance
    "availability":  0.12,  # Active on platform, willing to respond
    "experience_fit":0.08,  # 5-9 years sweet spot (not max years = best)
}


# ── Scoring functions ────────────────────────────────────────────────────────

def score_title_fit(candidate: Dict[str, Any]) -> float:
    """
    Scores how well the candidate's current title matches the AI/ML engineering role.
    Returns [0.0, 1.0].
    """
    title = candidate.get("profile", {}).get("current_title", "").lower()
    headline = candidate.get("profile", {}).get("headline", "").lower()
    combined = title + " " + headline

    for kw in DISQUALIFIER_TITLE_KEYWORDS:
        if kw in combined:
            return 0.0

    ai_matches = sum(1 for kw in POSITIVE_TITLE_KEYWORDS if kw in combined)
    if ai_matches >= 2:
        return 1.0
    elif ai_matches == 1:
        return 0.65
    return 0.35


def score_skill_overlap(candidate: Dict[str, Any], required_skills: List[str]) -> float:
    """
    Alias-aware skill overlap score using disjoint mapping checks in RankingService.
    """
    ratio, _, _ = _match_required_skills(required_skills, candidate)
    return ratio


def score_availability(candidate: Dict[str, Any]) -> float:
    """
    Composite availability score based on open_to_work, recency, response rates.
    """
    sig = candidate.get("redrob_signals", {})
    open_to_work = 1.0 if sig.get("open_to_work_flag", False) else 0.0

    last_active_str = sig.get("last_active_date", "")
    recency = 0.5
    if last_active_str:
        try:
            last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date()
            days_since = (date.today() - last_active).days
            recency = math.exp(-days_since / 90.0)
        except ValueError:
            pass

    response_rate = float(sig.get("recruiter_response_rate", 0.0))

    notice = int(sig.get("notice_period_days", 60))
    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.7
    elif notice <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.2

    return (
        0.40 * open_to_work
        + 0.30 * recency
        + 0.20 * response_rate
        + 0.10 * notice_score
    )


def score_experience_fit(candidate: Dict[str, Any]) -> float:
    """
    JD says 5-9 years sweet spot (bell curve centered at 7).
    """
    years = float(candidate.get("profile", {}).get("years_of_experience", 0.0))

    if years < 2:
        exp_score = 0.1
    elif years < 4:
        exp_score = 0.4
    elif years <= 9:
        exp_score = 1.0 - abs(years - 7) / 7.0
        exp_score = max(0.5, exp_score)
    elif years <= 12:
        exp_score = 0.6
    else:
        exp_score = 0.45

    current_company = candidate.get("profile", {}).get("current_company", "").lower()
    current_industry = candidate.get("profile", {}).get("current_industry", "").lower()
    is_consulting = (
        any(c in current_company for c in CONSULTING_COMPANIES)
        or "it services" in current_industry
        or "consulting" in current_industry
    )
    if is_consulting:
        exp_score *= 0.6

    return min(1.0, exp_score)


def compute_hybrid_score(
    candidate: Dict[str, Any],
    semantic_sim: float,
    required_skills: List[str]
) -> Tuple[float, Dict[str, float]]:
    """Compute the final hybrid score and per-component breakdown."""
    title_fit = score_title_fit(candidate)
    skill_overlap = score_skill_overlap(candidate, required_skills)
    availability = score_availability(candidate)
    exp_fit = score_experience_fit(candidate)

    overall = (
        WEIGHTS["semantic"]       * semantic_sim
        + WEIGHTS["skill_overlap"]  * skill_overlap
        + WEIGHTS["ai_title_fit"]   * title_fit
        + WEIGHTS["availability"]   * availability
        + WEIGHTS["experience_fit"] * exp_fit
    )

    components = {
        "semantic_sim":   round(semantic_sim, 4),
        "skill_overlap":  round(skill_overlap, 4),
        "title_fit":      round(title_fit, 4),
        "availability":   round(availability, 4),
        "exp_fit":        round(exp_fit, 4),
        "overall_score":  round(overall, 4),
    }
    return round(overall, 4), components


def generate_reasoning(candidate: Dict[str, Any], components: Dict[str, float]) -> str:
    """Generate a human-readable explanation of why this candidate was ranked."""
    profile = candidate.get("profile", {})
    title = profile.get("current_title", "Unknown title")
    company = profile.get("current_company", "Unknown company")
    years = profile.get("years_of_experience", 0)
    sig = candidate.get("redrob_signals", {})

    parts = []

    sem_pct = int(components["semantic_sim"] * 100)
    if sem_pct >= 70:
        parts.append(f"Strong semantic alignment with the AI/ML engineering role ({sem_pct}% match)")
    elif sem_pct >= 55:
        parts.append(f"Moderate semantic alignment with AI/ML engineering requirements ({sem_pct}% match)")
    else:
        parts.append(f"Partial semantic alignment ({sem_pct}% match)")

    tf = components["title_fit"]
    if tf >= 0.9:
        parts.append(f"role as {title} directly matches AI engineering profile")
    elif tf >= 0.6:
        parts.append(f"technical background as {title} is adjacent to AI engineering")
    else:
        parts.append(f"current title ({title}) is not a strong fit for this role")

    if years:
        industry = profile.get("current_industry", "")
        if "it services" in industry.lower() or "consulting" in industry.lower():
            parts.append(f"{years:.1f} years experience at {company} (IT services background, slight penalty applied)")
        else:
            parts.append(f"{years:.1f} years experience at {company}")

    overlap_pct = int(components["skill_overlap"] * 100)
    if overlap_pct >= 30:
        parts.append(f"{overlap_pct}% overlap with required AI/ML skills")
    elif overlap_pct > 0:
        parts.append(f"limited skill overlap ({overlap_pct}%) with required AI/ML skills")

    open_to_work = sig.get("open_to_work_flag", False)
    response_rate = sig.get("recruiter_response_rate", 0)
    last_active = sig.get("last_active_date", "")
    if open_to_work:
        parts.append("actively open to new opportunities")
    if response_rate >= 0.5:
        parts.append(f"high recruiter response rate ({int(response_rate*100)}%)")
    elif response_rate < 0.2:
        parts.append(f"low recruiter response rate ({int(response_rate*100)}%), availability risk")
    if last_active:
        try:
            days_since = (date.today() - datetime.strptime(last_active, "%Y-%m-%d").date()).days
            if days_since > 180:
                parts.append(f"profile inactive for {days_since} days")
        except ValueError:
            pass

    return ". ".join(parts) + "."


# ── Main Submission Pipeline ──────────────────────────────────────────────────

def main():
    default_jd_path = settings.get_absolute_path(
        os.path.join(settings.CHALLENGE_DATA_DIR, "job_description.docx")
    )
    
    parser = argparse.ArgumentParser(
        description="Final Challenge Submission Pipeline. Reads a JD, retrieves/ranks candidates, and validates output."
    )
    parser.add_argument(
        "--jd",
        type=str,
        default=default_jd_path,
        help=f"Path to job description (.docx or .txt). Default: {default_jd_path}",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../data/submissions/submission.csv",
        help="Path where the final ranked CSV will be written.",
    )
    parser.add_argument(
        "--top-k-retrieve",
        type=int,
        default=500,
        help="Number of candidates to retrieve from FAISS before hybrid re-ranking.",
    )
    parser.add_argument(
        "--top-k-rank",
        type=int,
        default=100,
        help="Number of top candidates to include in the final submission.",
    )
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info("=" * 70)
    logger.info("REDROB CHALLENGE SUBMISSION GENERATOR")
    logger.info(f"  JD Path    : {args.jd}")
    logger.info(f"  Output Path: {output_path}")
    logger.info("=" * 70)

    # 1. Read and parse Job Description
    logger.info("Reading and parsing job description file...")
    if not os.path.exists(args.jd):
        logger.error(f"Job description file not found at: {args.jd}")
        sys.exit(1)
        
    jd_text = read_job_description(args.jd)
    if not jd_text:
        logger.error("Job description text is empty. Aborting.")
        sys.exit(1)
        
    logger.info(f"Loaded {len(jd_text):,} characters of job description text.")

    # 2. Extract title & required skills
    title_match = re.search(r"Job Description:\s*(.*?)\s*(?:Company:|Location:|$)", jd_text, re.IGNORECASE)
    job_title = title_match.group(1).strip() if title_match else PRESET_JOB_TITLE
    
    # Check if this is the default founding AI engineer JD
    if "Senior AI Engineer" in job_title:
        logger.info(f"Identified default JD: '{job_title}'")
        required_skills = PRESET_REQUIRED_SKILLS
        semantic_query = PRESET_SEMANTIC_QUERY
    else:
        logger.info(f"Identified custom JD: '{job_title}'")
        required_skills = extract_skills_from_jd(jd_text)
        semantic_query = jd_text
        if len(required_skills) < 3:
            logger.warning("Fewer than 3 skills extracted. Falling back to default required skills.")
            required_skills = PRESET_REQUIRED_SKILLS

    logger.info(f"  Job Title:       '{job_title}'")
    logger.info(f"  Required Skills: {required_skills}")

    # 3. Load retrieval cache and FAISS index
    logger.info("Loading candidate cache and FAISS index...")
    ingestion = IngestionService()
    retrieval = RetrievalService()
    retrieval.load_index_and_cache(ingestion)

    if not retrieval.is_semantic_ready():
        logger.error("FAISS index not loaded — semantic retrieval unavailable. Build index first.")
        sys.exit(1)

    logger.info(f"  Retrieval mode: SEMANTIC ({len(retrieval.candidates_cache):,} candidates loaded)")

    # 4. Retrieve candidates via FAISS
    logger.info(f"Retrieving top {args.top_k_retrieve} candidates via FAISS semantic search...")
    candidates_with_scores = retrieval.retrieve_candidates(
        job_title=job_title,
        job_description=semantic_query,
        required_skills=required_skills,
        top_k=args.top_k_retrieve,
    )

    if not candidates_with_scores:
        logger.error("No candidates retrieved from FAISS. Aborting.")
        sys.exit(1)
        
    logger.info(f"  Retrieved {len(candidates_with_scores)} candidates for re-ranking.")

    # 5. Apply hybrid scoring
    logger.info("Applying hybrid candidate scoring and ranking...")
    scored: List[Tuple[float, str, Dict[str, Any], Dict[str, float]]] = []

    for cand, semantic_sim in candidates_with_scores:
        overall, components = compute_hybrid_score(cand, semantic_sim, required_skills)
        cand_id = cand.get("candidate_id", "")
        # Add tracking fields (single source of truth) to candidate dict for consistency
        cand["_skill_match_percent"] = int(components["skill_overlap"] * 100)
        scored.append((overall, cand_id, cand, components))

    # Sort: overall_score descending, candidate_id ascending for tie-break
    scored.sort(key=lambda x: (-x[0], x[1]))

    top_candidates = scored[: args.top_k_rank]

    all_scores = [s[0] for s in scored]
    logger.info(f"  Top candidate: {top_candidates[0][1]} (score: {top_candidates[0][0]:.4f})")
    logger.info(f"  Cut-off score (rank {args.top_k_rank}): {top_candidates[-1][0]:.4f}")

    # 6. Generate submission CSV
    logger.info("Writing submission CSV...")
    rows = []
    for rank_idx, (overall, cand_id, cand, components) in enumerate(top_candidates):
        reasoning = generate_reasoning(cand, components)
        rows.append({
            "candidate_id": cand_id,
            "rank": rank_idx + 1,
            "score": f"{overall:.4f}",
            "reasoning": reasoning,
        })

    df = pd.DataFrame(rows, columns=["candidate_id", "rank", "score", "reasoning"])
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved ranked submission containing {len(df)} rows to: {output_path}")

    # 7. Format Validation
    logger.info("Executing format validation check via challenge validate_submission.py...")
    challenge_dir = settings.get_absolute_path(settings.CHALLENGE_DATA_DIR)
    sys.path.append(challenge_dir)
    try:
        from validate_submission import validate_submission
        errors = validate_submission(output_path)
        if errors:
            logger.error(f"SUBMISSION FORMAT VALIDATION FAILED with {len(errors)} error(s):")
            for err in errors:
                logger.error(f"  - {err}")
            sys.exit(1)
        else:
            logger.info("=" * 70)
            logger.info("SUCCESS: SUBMISSION IS 100% VALID PER CHALLENGE RULES!")
            logger.info("=" * 70)
    except Exception as e:
        logger.warning(f"Could not import or run validate_submission.py: {e}")


if __name__ == "__main__":
    main()
