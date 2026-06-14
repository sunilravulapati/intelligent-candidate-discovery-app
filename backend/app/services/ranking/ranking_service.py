import re
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from app.ml.feature_engineering import XGBoostFeatureEngineer
from app.ml.ranker import CandidateRanker
from app.core.config import settings

logger = logging.getLogger(__name__)

# Default hybrid ranking weights — must sum to 1.0
DEFAULT_WEIGHTS: Dict[str, float] = {
    "semantic_similarity": 0.50,
    "skill_overlap":       0.20,
    "experience_match":    0.15,
    "activity_score":      0.15,
}


class RankingService:
    """
    Orchestrates candidate re-ranking via a hybrid weighted formula combining:
      - Semantic similarity (FAISS cosine score)
      - Skill overlap (Jaccard)
      - Experience match (years normalised)
      - Activity score (composite Redrob signals)

    Falls back to XGBoost / rule-based heuristic when semantic scores are absent.
    """

    def __init__(self, model_path: str = settings.RANKER_MODEL_PATH):
        self.feature_engineer = XGBoostFeatureEngineer()
        self.ranker = CandidateRanker(model_path=settings.get_absolute_path(model_path))
        self.ranker.load_model()

    # ── Component scorers ────────────────────────────────────────

    @staticmethod
    def _skill_overlap(required_skills: List[str], candidate: Dict[str, Any]) -> float:
        """Jaccard: required ∩ candidate / required (not true Jaccard, but per-spec)."""
        if not required_skills:
            return 0.0
        req_lower = {s.lower() for s in required_skills}
        cand_skills = {s.get("name", "").lower() for s in candidate.get("skills", [])}
        overlap = len(req_lower & cand_skills)
        return overlap / len(req_lower)

    @staticmethod
    def _experience_match(candidate: Dict[str, Any], max_years: float = 15.0) -> float:
        """Normalise years of experience to [0, 1], capped at max_years."""
        years = float(candidate.get("profile", {}).get("years_of_experience", 0.0))
        return min(years, max_years) / max_years

    @staticmethod
    def _activity_score(candidate: Dict[str, Any]) -> float:
        """
        Composite activity score from Redrob engagement signals.

        Weights:
          0.40 × open_to_work_flag        (binary)
          0.30 × profile_completeness / 100
          0.20 × recruiter_response_rate  (0-1)
          0.10 × github_activity / 100    (only when ≥ 0)
        """
        sig = candidate.get("redrob_signals", {})
        otw = 1.0 if sig.get("open_to_work_flag", False) else 0.0
        completeness = float(sig.get("profile_completeness_score", 0.0)) / 100.0
        response_rate = float(sig.get("recruiter_response_rate", 0.0))
        github_raw = float(sig.get("github_activity_score", -1.0))
        github = max(github_raw, 0.0) / 100.0 if github_raw >= 0 else 0.0

        return 0.40 * otw + 0.30 * completeness + 0.20 * response_rate + 0.10 * github

    # ── Main hybrid ranker ───────────────────────────────────────

    def hybrid_rank(
        self,
        required_skills: List[str],
        candidates_with_scores: List[Tuple[Dict[str, Any], float]],
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidates using a weighted hybrid of semantic + rule-based signals.

        Args:
            required_skills: Required skills from the job query.
            candidates_with_scores: List of (candidate_dict, semantic_score) from retrieval.
                                    semantic_score is 0.0 in keyword fallback mode.
            weights: Optional override for component weights. Falls back to DEFAULT_WEIGHTS.
            top_k: Number of candidates to return after ranking.

        Returns:
            List of candidate dicts enriched with scoring fields, sorted by overall_score desc.
        """
        w = weights or DEFAULT_WEIGHTS

        ranked: List[Dict[str, Any]] = []
        for cand, semantic_sim in candidates_with_scores:
            skill_ov = self._skill_overlap(required_skills, cand)
            exp_match = self._experience_match(cand)
            act_score = self._activity_score(cand)

            overall = (
                w.get("semantic_similarity", 0.0) * semantic_sim
                + w.get("skill_overlap", 0.0) * skill_ov
                + w.get("experience_match", 0.0) * exp_match
                + w.get("activity_score", 0.0) * act_score
            )

            cand_copy = cand.copy()
            cand_copy["_semantic_similarity"] = round(semantic_sim, 4)
            cand_copy["_skill_overlap"]       = round(skill_ov, 4)
            cand_copy["_experience_match"]    = round(exp_match, 4)
            cand_copy["_activity_score"]      = round(act_score, 4)
            cand_copy["overall_score"]        = round(overall, 4)
            cand_copy["skills_match_percent"] = int(skill_ov * 100)
            cand_copy["semantic_similarity_percent"] = int(semantic_sim * 100)
            ranked.append(cand_copy)

        # Sort: overall_score desc, then candidate_id asc for determinism
        ranked.sort(key=lambda x: (-x["overall_score"], x["candidate_id"]))
        return ranked[:top_k]

    # ── Legacy XGBoost path (kept for compatibility) ─────────────

    def rank_retrieved_candidates(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Legacy XGBoost-based ranking. Used when no semantic scores are available
        and the XGBoost model file exists. Otherwise falls back to rule heuristic.
        """
        if not candidates:
            return []

        job_query = {
            "title": job_title,
            "description": job_description,
            "required_skills": required_skills,
        }
        feature_df = self.feature_engineer.batch_extract_features(job_query, candidates)
        scores = self.ranker.predict_scores(feature_df)
        return self.ranker.rank_candidates(candidates, scores)
