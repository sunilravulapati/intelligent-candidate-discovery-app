import time
import re
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.services.ingestion.ingestion_service import IngestionService
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
    current_title: str
    rank: int
    # Legacy field kept for backward-compatibility — equals overall_score
    match_score: float
    # Fit dimensions (0-100)
    role_fit_percent: int
    skill_fit_percent: int
    semantic_fit_percent: int
    # Semantic retrieval score
    semantic_similarity_percent: int
    # Title alignment score
    title_alignment_percent: int
    # Skill overlap
    skills_match_percent: int
    matched_skills: List[str]
    missing_skills: List[str]
    ranking_reasons: List[str]
    # Experience normalised score (0-1)
    experience_score: float
    # Activity composite score (0-1)
    activity_score: float
    # Final hybrid weighted score (0-1)
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
    embedding_time_ms: int = 0
    faiss_time_ms: int = 0
    ranking_time_ms: int
    explainability_time_ms: int = 0
    total_time_ms: int
    retrieval_mode: str
    embedding_cache_hit: bool = False
    embedding_calls_per_request: int = 0
    embedding_calls_per_session: int = 0
    embedding_cache_hits_per_session: int = 0
    embedding_cache_misses_per_session: int = 0
    top_skills_found: List[str]
    timing_breakdown: Dict[str, float] = Field(default_factory=dict)


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
          ↓ RankingService.hybrid_rank()              [0.28×role + 0.30×skill + 0.27×sem + 0.10×exp + 0.05×act]
          ↓ ExplainabilityService.generate_explanation()
          ↓ Top-K results
    """
    t_start = time.time()
    logger.info("Timing - Request received")

    # 1. Resolve required skills
    req_skills = request.required_skills or []
    if not req_skills:
        req_skills = _fallback_skill_parse(request.description)

    # 2. Ensure candidate cache + FAISS index loaded (idempotent)
    t_load_start = time.time()
    try:
        retrieval.load_index_and_cache(ingestion)
    except Exception as e:
        logger.error(f"Failed to load candidate cache / index: {e}")
        raise HTTPException(status_code=500, detail=f"Candidate loading failed: {str(e)}")
    t_load_end = time.time()
    logger.info(f"Timing - Load index and cache check: {(t_load_end - t_load_start)*1000:.2f} ms")

    if not retrieval.candidates_cache:
        return JobSearchResponse(
            metrics=SearchMetrics(
                candidates_indexed=0,
                retrieval_pool_size=0,
                avg_match_score=0.0,
                retrieval_time_ms=0,
                embedding_time_ms=0,
                faiss_time_ms=0,
                ranking_time_ms=0,
                explainability_time_ms=0,
                total_time_ms=0,
                retrieval_mode="keyword",
                top_skills_found=[],
            ),
            results=[],
        )

    retrieval_mode = "semantic" if retrieval.is_semantic_ready() else "keyword"
    timing_breakdown = {
        "Query Embedding": 0.0,
        "FAISS Retrieval": 0.0,
        "Candidate Ranking": 0.0,
        "Explainability Generation": 0.0,
        "Embedding Cache Hit": 0.0,
        "Embedding Calls This Request": 0.0,
        "Embedding Calls This Session": 0.0,
        "Embedding Cache Hits This Session": 0.0,
        "Embedding Cache Misses This Session": 0.0,
    }

    # 3. Retrieve candidate pool
    t_retrieval_start = time.time()

    if retrieval.is_semantic_ready():
        # Semantic: FAISS top-500 pre-filter
        candidates_with_scores, ret_timings = retrieval.retrieve_candidates(
            job_title=request.title,
            job_description=request.description,
            required_skills=req_skills,
            top_k=500,
            return_timings=True,
        )
        timing_breakdown["Query Embedding"] = ret_timings.get("Query Embedding", 0.0)
        timing_breakdown["FAISS Retrieval"] = ret_timings.get("FAISS Retrieval", 0.0)
        timing_breakdown["Embedding Cache Hit"] = ret_timings.get("Embedding Cache Hit", 0.0)
        timing_breakdown["Embedding Calls This Request"] = ret_timings.get("Embedding Calls This Request", 0.0)
        timing_breakdown["Embedding Calls This Session"] = ret_timings.get("Embedding Calls This Session", 0.0)
        timing_breakdown["Embedding Cache Hits This Session"] = ret_timings.get("Embedding Cache Hits This Session", 0.0)
        timing_breakdown["Embedding Cache Misses This Session"] = ret_timings.get("Embedding Cache Misses This Session", 0.0)
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

    t_retrieval_end = time.time()
    t_retrieval_ms = int((t_retrieval_end - t_retrieval_start) * 1000)
    logger.info(f"Timing - Total retrieval step (including encoding & FAISS): {t_retrieval_ms:.2f} ms")
    pool_size = len(candidates_with_scores)

    # 4. Hybrid ranking → top 100
    t_rank_start = time.time()
    ranked = ranking.hybrid_rank(
        required_skills=req_skills,
        candidates_with_scores=candidates_with_scores,
        top_k=100,
        job_title=request.title,
    )
    t_rank_end = time.time()
    t_rank_ms = (t_rank_end - t_rank_start) * 1000
    timing_breakdown["Candidate Ranking"] = round(t_rank_ms, 2)
    logger.info(f"Timing - Hybrid ranking: {t_rank_ms:.2f} ms")

    # 5. Slice to requested top_k and build response
    top_candidates = ranked[: request.top_k]
    results: List[CandidateMatchResponse] = []
    scores: List[float] = []
    skills_freq: Dict[str, int] = {}

    t_explain_start = time.time()
    for rank_idx, cand in enumerate(top_candidates, start=1):
        profile = cand.get("profile", {})
        overall = cand.get("overall_score", 0.0)
        sem_pct = cand.get("semantic_similarity_percent", 0)
        title_pct = cand.get("title_alignment_percent", 0)
        skill_pct = cand.get("_skill_match_percent", 0)
        semantic_sim = cand.get("_semantic_similarity", 0.0)
        scores.append(overall)

        matched_skills = list(cand.get("_matched_skills") or [])
        missing_skills = list(cand.get("_missed_skills") or [])

        for s in cand.get("skills", []):
            sn = s.get("name", "")
            if sn:
                skills_freq[sn] = skills_freq.get(sn, 0) + 1

        ranking_reasons = explainability.generate_ranking_reasons(
            job_title=request.title,
            required_skills=req_skills,
            candidate=cand,
            semantic_similarity=semantic_sim if retrieval_mode == "semantic" else None,
            rank=rank_idx,
        )

        explanation = explainability.generate_explanation(
            job_title=request.title,
            required_skills=req_skills,
            candidate=cand,
            semantic_similarity=semantic_sim if retrieval_mode == "semantic" else None,
            rank=rank_idx,
        )

        current_title = profile.get("current_title", "") or profile.get("headline", "")

        results.append(
            CandidateMatchResponse(
                candidate_id=cand.get("candidate_id", ""),
                name=profile.get("anonymized_name", "Anonymous Candidate"),
                headline=profile.get("headline", ""),
                current_title=current_title,
                rank=rank_idx,
                match_score=round(overall, 2),
                role_fit_percent=title_pct,
                skill_fit_percent=skill_pct,
                semantic_fit_percent=sem_pct,
                semantic_similarity_percent=sem_pct,
                title_alignment_percent=title_pct,
                skills_match_percent=skill_pct,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                ranking_reasons=ranking_reasons,
                experience_score=round(cand.get("_experience_match", 0.0), 4),
                activity_score=round(cand.get("_activity_score", 0.0), 4),
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
    t_explain_end = time.time()
    t_explain_ms = (t_explain_end - t_explain_start) * 1000
    timing_breakdown["Explainability Generation"] = round(t_explain_ms, 2)
    logger.info(f"Timing - Explanation generation: {t_explain_ms:.2f} ms")

    t_total_ms = int((time.time() - t_start) * 1000)
    top_skills = sorted(skills_freq, key=lambda k: skills_freq[k], reverse=True)[:5]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    metrics = SearchMetrics(
        candidates_indexed=len(retrieval.candidates_cache),
        retrieval_pool_size=pool_size,
        avg_match_score=avg_score,
        retrieval_time_ms=t_retrieval_ms,
        embedding_time_ms=int(timing_breakdown["Query Embedding"]),
        faiss_time_ms=int(timing_breakdown["FAISS Retrieval"]),
        ranking_time_ms=int(t_rank_ms),
        explainability_time_ms=int(t_explain_ms),
        total_time_ms=t_total_ms,
        retrieval_mode=retrieval_mode,
        embedding_cache_hit=bool(timing_breakdown["Embedding Cache Hit"]),
        embedding_calls_per_request=int(timing_breakdown["Embedding Calls This Request"]),
        embedding_calls_per_session=int(timing_breakdown["Embedding Calls This Session"]),
        embedding_cache_hits_per_session=int(timing_breakdown["Embedding Cache Hits This Session"]),
        embedding_cache_misses_per_session=int(timing_breakdown["Embedding Cache Misses This Session"]),
        top_skills_found=top_skills,
        timing_breakdown=timing_breakdown,
    )

    # Log/Print timing breakdown to the backend console
    print("\n================ TIMING BREAKDOWN ================")
    print(f"Query Embedding: {timing_breakdown['Query Embedding']:.2f}ms")
    print(f"Embedding Calls / Request: {int(timing_breakdown['Embedding Calls This Request'])}")
    print(f"Embedding Calls / Session: {int(timing_breakdown['Embedding Calls This Session'])}")
    print(f"Embedding Cache Hit: {bool(timing_breakdown['Embedding Cache Hit'])}")
    print(f"FAISS Retrieval: {timing_breakdown['FAISS Retrieval']:.2f}ms")
    print(f"Candidate Ranking: {timing_breakdown['Candidate Ranking']:.2f}ms")
    print(f"Explainability Generation: {timing_breakdown['Explainability Generation']:.2f}ms")
    print("==================================================\n")

    response_obj = JobSearchResponse(metrics=metrics, results=results)
    return response_obj
