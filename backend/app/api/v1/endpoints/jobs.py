import time
import re
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.services.ingestion.ingestion_service import IngestionService
from app.services.embeddings.embeddings_service import EmbeddingsService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import RankingService
from app.services.explainability.explainability_service import ExplainabilityService

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ─────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    title: str = Field(..., description="Job title for matching", example="Backend Engineer")
    description: str = Field(
        ...,
        description="Full job description",
        example="Looking for Python engineer with FastAPI, FAISS, and ML experience.",
    )
    required_skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional explicit skills list",
        example=["Python", "FastAPI"],
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")


class CandidateMatchResponse(BaseModel):
    candidate_id: str
    name: str
    headline: str
    # Legacy field kept for backward-compatibility — equals overall_score
    match_score: float
    # Semantic retrieval score
    semantic_similarity_percent: int
    # Title alignment score
    title_alignment_percent: int
    # Skill Jaccard overlap
    skills_match_percent: int
    # Final hybrid weighted score
    overall_score: float
    years_of_experience: float
    current_company: str
    explanation: str
    retrieval_mode: str  # "semantic" or "keyword"
    # Full profile details (for Drawer UI)
    skills: List[Dict[str, Any]]
    career_history: List[Dict[str, Any]]
    redrob_signals: Dict[str, Any]


class SearchMetrics(BaseModel):
    candidates_indexed: int
    retrieval_pool_size: int
    avg_match_score: float
    retrieval_time_ms: int
    ranking_time_ms: int
    total_time_ms: int
    retrieval_mode: str
    top_skills_found: List[str]


class JobSearchResponse(BaseModel):
    metrics: SearchMetrics
    results: List[CandidateMatchResponse]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> set:
    if not text:
        return set()
    return set(re.findall(r'\b\w+\b', text.lower()))


def _jaccard_title_similarity(job_title: str, candidate_title: str) -> float:
    a = _tokenize(job_title)
    b = _tokenize(candidate_title)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _fallback_skill_parse(description: str) -> List[str]:
    """Last-resort: extract common tech skills from free-form description text."""
    common = [
        "python", "fastapi", "react", "typescript", "postgres", "sql", "aws",
        "docker", "spark", "kubernetes", "xgboost", "machine learning", "pytorch",
        "tensorflow", "redis", "kafka", "go", "java", "node", "django", "flask",
    ]
    desc_lower = description.lower()
    return [s.capitalize() for s in common if s in desc_lower] or ["Python"]


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/jobs", response_model=JobSearchResponse)
def match_candidates(
    request: JobSearchRequest,
    ingestion: IngestionService = Depends(deps.get_ingestion_service),
    embeddings: EmbeddingsService = Depends(deps.get_embeddings_service),
    retrieval: RetrievalService = Depends(deps.get_retrieval_service),
    ranking: RankingService = Depends(deps.get_ranking_service),
    explainability: ExplainabilityService = Depends(deps.get_explainability_service),
):
    """
    Retrieves and ranks matching candidates for a job description.

    Pipeline:
        Job Query
          ↓ [Skill parse fallback if empty]
          ↓ RetrievalService.load_index_and_cache()   [once, cached in memory]
          ↓ RetrievalService.retrieve_candidates()    [FAISS top-500 or full keyword scan]
          ↓ RankingService.hybrid_rank()              [0.35×sem + 0.20×title + 0.30×skill + 0.10×exp + 0.05×act]
          ↓ ExplainabilityService.generate_explanation()
          ↓ Top-K results
    """
    t_start = time.time()

    # 1. Resolve required skills
    req_skills = request.required_skills or []
    if not req_skills:
        req_skills = _fallback_skill_parse(request.description)

    # 2. Ensure candidate cache + FAISS index loaded (idempotent)
    try:
        retrieval.load_index_and_cache(ingestion)
    except Exception as e:
        logger.error(f"Failed to load candidate cache / index: {e}")
        raise HTTPException(status_code=500, detail=f"Candidate loading failed: {str(e)}")

    if not retrieval.candidates_cache:
        return JobSearchResponse(
            metrics=SearchMetrics(
                candidates_indexed=0,
                retrieval_pool_size=0,
                avg_match_score=0.0,
                retrieval_time_ms=0,
                ranking_time_ms=0,
                total_time_ms=0,
                retrieval_mode="keyword",
                top_skills_found=[],
            ),
            results=[],
        )

    retrieval_mode = "semantic" if retrieval.is_semantic_ready() else "keyword"

    # 3. Retrieve candidate pool
    t_retrieval_start = time.time()

    if retrieval.is_semantic_ready():
        # Semantic: FAISS top-500 pre-filter
        candidates_with_scores = retrieval.retrieve_candidates(
            job_title=request.title,
            job_description=request.description,
            required_skills=req_skills,
            top_k=500,
        )
    else:
        # Keyword fallback: full scan — all candidates with semantic_score=0.0
        job_title_tokens = _tokenize(request.title)
        req_skills_lower = {s.lower() for s in req_skills}
        candidates_with_scores = []
        for cand in retrieval.candidates_cache.values():
            cand_skills_lower = {s.get("name", "").lower() for s in cand.get("skills", [])}
            skill_ov = len(req_skills_lower & cand_skills_lower) / max(len(req_skills_lower), 1)
            cand_title = cand.get("profile", {}).get("current_title", "")
            title_sim = _jaccard_title_similarity(request.title, cand_title)
            # Use baseline Jaccard score as the semantic proxy in keyword mode
            baseline = 0.6 * skill_ov + 0.4 * title_sim
            candidates_with_scores.append((cand, baseline))

    t_retrieval_ms = int((time.time() - t_retrieval_start) * 1000)
    pool_size = len(candidates_with_scores)

    # 4. Hybrid ranking → top 100
    t_rank_start = time.time()
    ranked = ranking.hybrid_rank(
        required_skills=req_skills,
        candidates_with_scores=candidates_with_scores,
        top_k=100,
        job_title=request.title,
    )
    t_rank_ms = int((time.time() - t_rank_start) * 1000)

    # 5. Slice to requested top_k and build response
    top_candidates = ranked[: request.top_k]
    results: List[CandidateMatchResponse] = []
    scores: List[float] = []
    skills_freq: Dict[str, int] = {}

    for cand in top_candidates:
        profile = cand.get("profile", {})
        overall = cand.get("overall_score", 0.0)
        sem_pct = cand.get("semantic_similarity_percent", 0)
        title_pct = cand.get("title_alignment_percent", 0)
        skill_pct = cand.get("_skill_match_percent", 0)
        semantic_sim = cand.get("_semantic_similarity", 0.0)
        scores.append(overall)

        for s in cand.get("skills", []):
            sn = s.get("name", "")
            if sn:
                skills_freq[sn] = skills_freq.get(sn, 0) + 1

        explanation = explainability.generate_explanation(
            job_title=request.title,
            required_skills=req_skills,
            candidate=cand,
            semantic_similarity=semantic_sim if retrieval_mode == "semantic" else None,
        )

        results.append(
            CandidateMatchResponse(
                candidate_id=cand.get("candidate_id", ""),
                name=profile.get("anonymized_name", "Anonymous Candidate"),
                headline=profile.get("headline", ""),
                match_score=round(overall, 2),
                semantic_similarity_percent=sem_pct,
                title_alignment_percent=title_pct,
                skills_match_percent=skill_pct,
                overall_score=round(overall, 4),
                years_of_experience=profile.get("years_of_experience", 0.0),
                current_company=profile.get("current_company", "N/A"),
                explanation=explanation,
                retrieval_mode=retrieval_mode,
                skills=cand.get("skills", []),
                career_history=cand.get("career_history", []),
                redrob_signals=cand.get("redrob_signals", {}),
            )
        )

    t_total_ms = int((time.time() - t_start) * 1000)
    top_skills = sorted(skills_freq, key=lambda k: skills_freq[k], reverse=True)[:5]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    metrics = SearchMetrics(
        candidates_indexed=len(retrieval.candidates_cache),
        retrieval_pool_size=pool_size,
        avg_match_score=avg_score,
        retrieval_time_ms=t_retrieval_ms,
        ranking_time_ms=t_rank_ms,
        total_time_ms=t_total_ms,
        retrieval_mode=retrieval_mode,
        top_skills_found=top_skills,
    )

    return JobSearchResponse(metrics=metrics, results=results)
