import logging
from typing import List, Dict, Any, Optional, Set, Tuple

from app.ml.feature_engineering import XGBoostFeatureEngineer
from app.ml.ranker import CandidateRanker
from app.ml.title_scorer import TitleAlignmentScorer
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Skill alias map ────────────────────────────────────────────────────────────
# Maps every canonical required-skill token to a set of accepted aliases.
# All strings are lowercase.  During matching we check whether ANY alias appears
# in the candidate's combined skill+text corpus.

_SKILL_ALIASES: Dict[str, Set[str]] = {
    # Languages
    "python":           {"python", "py", "python3", "python 3"},
    "javascript":       {"javascript", "js", "es6", "es2015", "ecmascript"},
    "typescript":       {"typescript", "ts"},
    "java":             {"java", "java8", "java11", "java 17", "java ee"},
    "go":               {"go", "golang"},
    "rust":             {"rust", "rustlang"},
    "c++":              {"c++", "cpp", "c plus plus"},
    "c#":               {"c#", "csharp", "dotnet", ".net", "asp.net"},
    "kotlin":           {"kotlin"},
    "swift":            {"swift"},
    "scala":            {"scala"},
    "ruby":             {"ruby"},
    "php":              {"php"},
    "r":                {"r", "r language", "rlang"},
    # Web frameworks
    "fastapi":          {"fastapi", "fast api"},
    "django":           {"django"},
    "flask":            {"flask"},
    "express":          {"express", "express.js", "expressjs"},
    "spring":           {"spring", "spring boot", "spring framework"},
    "rails":            {"rails", "ruby on rails"},
    "nextjs":           {"next.js", "nextjs", "next js"},
    "react":            {"react", "reactjs", "react.js"},
    "vue":              {"vue", "vuejs", "vue.js"},
    "angular":          {"angular", "angularjs", "angular.js"},
    # Databases
    "postgresql":       {"postgresql", "postgres", "psql", "pg"},
    "mysql":            {"mysql", "mariadb"},
    "mongodb":          {"mongodb", "mongo"},
    "redis":            {"redis"},
    "elasticsearch":    {"elasticsearch", "elastic search", "es", "opensearch", "open search"},
    "cassandra":        {"cassandra", "apache cassandra"},
    "sqlite":           {"sqlite", "sqlite3"},
    "dynamodb":         {"dynamodb", "dynamo"},
    "neo4j":            {"neo4j", "graph database"},
    "oracle":           {"oracle", "oracle db"},
    "mssql":            {"mssql", "sql server", "microsoft sql"},
    # Cloud & infra
    "aws":              {"aws", "amazon web services", "ec2", "s3", "lambda", "cloudformation"},
    "gcp":              {"gcp", "google cloud", "google cloud platform", "bigquery"},
    "azure":            {"azure", "microsoft azure"},
    "docker":           {"docker", "dockerfile", "containerization"},
    "kubernetes":       {"kubernetes", "k8s", "helm", "kubectl"},
    "terraform":        {"terraform"},
    "ansible":          {"ansible"},
    # ML / AI
    "faiss":            {"faiss", "facebook ai similarity search"},
    "pytorch":          {"pytorch", "torch"},
    "tensorflow":       {"tensorflow", "tf", "keras"},
    "scikit-learn":     {"scikit-learn", "scikit learn", "sklearn"},
    "huggingface":      {"huggingface", "transformers", "sentence-transformers", "sentence transformers"},
    "xgboost":          {"xgboost", "xgb", "gradient boosting"},
    "lightgbm":         {"lightgbm", "lgbm"},
    "nlp":              {"nlp", "natural language processing", "text mining"},
    "spacy":            {"spacy"},
    "nltk":             {"nltk"},
    "embeddings":       {"embeddings", "embedding"},
    "retrieval":        {"retrieval", "retrieval systems", "dense retrieval"},
    "vector search":    {"vector search", "vector database", "vector db", "vector databases"},
    "ranking":          {"ranking", "re-ranking", "reranking", "ranking systems"},
    "recommendation":   {"recommendation", "recommendations", "recommendation systems", "recommendation engine"},
    "information retrieval": {"information retrieval", "ir"},
    "evaluation":       {"evaluation", "evals", "eval"},
    "ndcg":             {"ndcg"},
    "mrr":              {"mrr"},
    "map":              {"map"},
    "learning to rank": {"learning to rank", "learning-to-rank", "ltr"},
    "hybrid search":    {"hybrid search", "hybrid retrieval"},
    "milvus":           {"milvus"},
    # Data & streaming
    "spark":            {"spark", "apache spark", "pyspark"},
    "kafka":            {"kafka", "apache kafka"},
    "airflow":          {"airflow", "apache airflow"},
    "dbt":              {"dbt", "data build tool"},
    "pandas":           {"pandas", "pd"},
    "numpy":            {"numpy", "np"},
    # API patterns
    "rest api":         {"rest api", "rest", "restful", "restful api", "http api"},
    "graphql":          {"graphql", "graphql api"},
    "grpc":             {"grpc", "protobuf", "protocol buffers"},
    # Message queues
    "rabbitmq":         {"rabbitmq", "rabbit mq"},
    "celery":           {"celery"},
    # Search
    "solr":             {"solr", "apache solr"},
    "vector search":    {"vector search", "vector database", "vector db"},
    "pinecone":         {"pinecone"},
    "weaviate":         {"weaviate"},
    "qdrant":           {"qdrant"},
    # Testing
    "pytest":           {"pytest", "unit testing", "testing"},
    "git":              {"git", "github", "gitlab", "version control"},
    # Monitoring
    "prometheus":       {"prometheus"},
    "grafana":          {"grafana"},
    # Other common
    "microservices":    {"microservices", "microservice", "micro services", "service mesh"},
    "sql":              {"sql", "rdbms", "relational database"},
    "api design":       {"api design", "api development", "rest design"},
    "oauth":            {"oauth", "oauth2", "jwt", "authentication", "authorization"},
    "swagger":          {"swagger", "api docs"},
    "openapi":          {"openapi", "open api"},
    "ci/cd":            {"ci/cd", "cicd", "continuous integration", "jenkins", "github actions", "gitlab ci"},
    "linux":            {"linux", "unix", "bash", "shell scripting"},
    "node.js":          {"node.js", "nodejs", "node js", "npm"},
}

# Build a reverse lookup: alias → canonical name
_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, aliases in _SKILL_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias] = canonical


def _normalise_skill(skill: str) -> str:
    """Lower-case and strip a skill string."""
    return skill.lower().strip()


def _canonical(skill: str) -> str:
    """Return the canonical alias group for a skill (or itself if not in map)."""
    norm = _normalise_skill(skill)
    return _ALIAS_TO_CANONICAL.get(norm, norm)


def _build_candidate_corpus(candidate: Dict[str, Any]) -> str:
    """
    Build a single searchable text blob from a candidate's skills + summary +
    headline.  Used as the full-text fallback when exact skill matching fails.
    """
    skill_names = " ".join(
        s.get("name", "").lower() for s in candidate.get("skills", [])
    )
    profile = candidate.get("profile", {})
    summary  = (profile.get("summary")  or "").lower()
    headline = (profile.get("headline") or "").lower()
    return f"{skill_names} {headline} {summary}"


def _match_required_skills(
    required_skills: List[str],
    candidate: Dict[str, Any],
) -> Tuple[float, List[str], List[str]]:
    """
    Compute skill overlap ratio and return which skills matched / missed.

    Matching strategy (in priority order):
      1. Canonical alias lookup — maps known aliases to the same group
      2. Substring presence in the candidate's full-text corpus

    Returns:
        (ratio, matched_skills, missed_skills)
        ratio = matched / len(required_skills)  [0.0 .. 1.0]
    """
    if not required_skills:
        return 0.0, [], []

    corpus = _build_candidate_corpus(candidate)

    # Build canonical candidate skill set (from structured skill list)
    cand_skill_canonicals: Set[str] = {
        _canonical(s.get("name", "")) for s in candidate.get("skills", [])
    }

    matched: List[str] = []
    missed:  List[str] = []

    for req_skill in required_skills:
        req_canonical = _canonical(req_skill)

        # Strategy 1: canonical alias group match
        if req_canonical in cand_skill_canonicals:
            matched.append(req_skill)
            continue

        # Strategy 2: check all aliases in corpus (substring)
        req_aliases = _SKILL_ALIASES.get(req_canonical, {_normalise_skill(req_skill)})
        found_in_text = any(alias in corpus for alias in req_aliases)
        if found_in_text:
            matched.append(req_skill)
        else:
            missed.append(req_skill)

    ratio = len(matched) / len(required_skills)
    return round(ratio, 4), matched, missed


# ── Default weights — role/skill/semantic first, activity last ────────────────
# Prioritises Role Fit > Skill Fit > Semantic Fit over engagement signals.
# Activity is gated by role+skill fit so it cannot lift unrelated profiles.

DEFAULT_WEIGHTS: Dict[str, float] = {
    "title_alignment":     0.35,  # Role Fit
    "skill_overlap":       0.30,  # Skill Fit
    "semantic_similarity": 0.20,  # Semantic Fit
    "experience_match":    0.10,
    "activity_score":      0.05,
}


class RankingService:
    """
    Orchestrates candidate re-ranking via a hybrid weighted formula combining:
      - Title alignment      (role-family + token match) weight=0.28
      - Skill overlap        (alias-aware matching)      weight=0.30
      - Semantic similarity  (FAISS cosine score)        weight=0.27
      - Experience match     (years normalised)          weight=0.10
      - Activity score       (gated by role+skill fit)   weight=0.05

    Falls back to XGBoost / rule-based heuristic when semantic scores are absent.
    """

    def __init__(self, model_path: str = settings.RANKER_MODEL_PATH):
        self.feature_engineer = XGBoostFeatureEngineer()
        self.ranker = CandidateRanker(model_path=settings.get_absolute_path(model_path))
        self.ranker.load_model()
        self._title_scorer = TitleAlignmentScorer()
        self.last_timing_breakdown: Dict[str, float] = {}

    # ── Component scorers ────────────────────────────────────────

    @staticmethod
    def _skill_overlap(
        required_skills: List[str],
        candidate: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        """
        Alias-aware skill overlap.

        Returns (ratio, matched_skills, missed_skills).
        ratio = len(matched) / len(required_skills)
        """
        return _match_required_skills(required_skills, candidate)

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

    def _title_alignment(self, job_title: str, candidate: Dict[str, Any]) -> float:
        """Normalized [0, 1] title alignment using TitleAlignmentScorer."""
        score, _ = self._title_scorer.score_candidate(job_title, candidate)
        return score

    # ── Main hybrid ranker ───────────────────────────────────────

    def hybrid_rank(
        self,
        required_skills: List[str],
        candidates_with_scores: List[Tuple[Dict[str, Any], float]],
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 100,
        job_title: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidates using a weighted hybrid of semantic + rule-based signals.

        Args:
            required_skills: Required skills from the job query.
            candidates_with_scores: List of (candidate_dict, semantic_score) from retrieval.
                                    semantic_score is 0.0 in keyword fallback mode.
            weights: Optional override for component weights. Falls back to DEFAULT_WEIGHTS.
            top_k: Number of candidates to return after ranking.
            job_title: Job title string — required for title_alignment scoring.

        Returns:
            List of candidate dicts enriched with scoring fields, sorted by overall_score desc.
        """
        import time
        w = weights or DEFAULT_WEIGHTS

        # Precompute query-level parameters for title alignment
        from app.ml.title_scorer import _tokenize, _family_of, _seniority_tier
        job_tok = _tokenize(job_title)
        job_family = _family_of(job_title)
        job_tier = _seniority_tier(job_tok)

        # Precompute query-level parameters for skill matching
        required_canonical_map = { _canonical(s): s for s in required_skills }
        required_canonicals = set(required_canonical_map)
        required_dynamic_canonicals = { c for c in required_canonical_map if c not in _SKILL_ALIASES }

        # Cumulative timing buckets in milliseconds
        t_title_alignment = 0.0
        t_skill_match = 0.0
        t_alias_resolution = 0.0
        t_experience = 0.0
        t_semantic = 0.0
        t_aggregation = 0.0
        t_sorting = 0.0

        ranked: List[Dict[str, Any]] = []
        t_rank_start = time.perf_counter()
        for cand, semantic_sim in candidates_with_scores:
            # 1. Title alignment (O(1) lookup + math)
            t0 = time.perf_counter()
            if "candidate_title_tokens" in cand:
                title_align = self._title_scorer.score_precomputed(
                    job_tok,
                    job_family,
                    job_tier,
                    cand["candidate_title_tokens"],
                    cand["candidate_title_family"],
                    cand["candidate_title_tier"],
                )
            else:
                title_align = self._title_alignment(job_title, cand)
            t_title_alignment += (time.perf_counter() - t0) * 1000

            # 2. Skill overlap (O(1) set intersections + dynamic search)
            # We measure strategy 1 (explicit skill match) under skill_match,
            # and strategy 2 (alias and dynamic skill text scans) under alias_resolution.
            t0 = time.perf_counter()
            if "candidate_explicit_skills" in cand:
                matched_explicit = required_canonicals & cand["candidate_explicit_skills"]
                t_skill_match += (time.perf_counter() - t0) * 1000

                t0 = time.perf_counter()
                matched_aliases = required_canonicals & cand["candidate_alias_skills"]

                matched = matched_explicit | matched_aliases
                for rc in required_dynamic_canonicals:
                    if rc not in matched:
                        if rc in cand["candidate_corpus"]:
                            matched.add(rc)

                matched_skills = [required_canonical_map[mc] for mc in matched]
                missed_skills = [orig for mc, orig in required_canonical_map.items() if mc not in matched]

                skill_ratio = len(matched_skills) / len(required_skills) if required_skills else 0.0
                t_alias_resolution += (time.perf_counter() - t0) * 1000
            else:
                # Fallback to legacy path if cache is somehow not loaded/precomputed
                skill_ratio, matched_skills, missed_skills = self._skill_overlap(required_skills, cand)
                t_skill_match += (time.perf_counter() - t0) * 1000

            # 3. Experience Scoring Time
            t0 = time.perf_counter()
            exp_match = cand.get("candidate_experience_match")
            if exp_match is None:
                exp_match = self._experience_match(cand)
            t_experience += (time.perf_counter() - t0) * 1000

            # 4. Semantic Score Calculation Time
            t0 = time.perf_counter()
            contrib_semantic = w.get("semantic_similarity", 0.0) * semantic_sim
            t_semantic += (time.perf_counter() - t0) * 1000

            # 5. Final Score Aggregation Time
            t0 = time.perf_counter()
            act_score = cand.get("candidate_activity_score")
            if act_score is None:
                act_score = self._activity_score(cand)
            fit_gate = min(1.0, (title_align * 0.55 + skill_ratio * 0.45))
            effective_act = act_score * fit_gate

            overall = min(
                w.get("title_alignment",     0.0) * title_align
                + w.get("skill_overlap",       0.0) * skill_ratio
                + contrib_semantic
                + w.get("experience_match",    0.0) * exp_match
                + w.get("activity_score",      0.0) * effective_act,
                1.0,
            )

            # Component contributions
            contrib_title = w.get("title_alignment",     0.0) * title_align
            contrib_skill = w.get("skill_overlap",       0.0) * skill_ratio
            contrib_exp   = w.get("experience_match",    0.0) * exp_match
            contrib_act   = w.get("activity_score",      0.0) * effective_act

            cand_copy = cand.copy()
            # Raw component scores
            cand_copy["_semantic_similarity"]      = round(semantic_sim, 4)
            cand_copy["_title_alignment"]          = round(title_align, 4)
            cand_copy["_skill_overlap"]            = round(skill_ratio, 4)
            cand_copy["_experience_match"]         = round(exp_match, 4)
            cand_copy["_activity_score"]           = round(act_score, 4)
            cand_copy["_activity_effective"]       = round(effective_act, 4)
            cand_copy["_activity_fit_gate"]        = round(fit_gate, 4)
            # Weighted contributions
            cand_copy["_contrib_title"]            = round(contrib_title, 4)
            cand_copy["_contrib_semantic"]         = round(contrib_semantic, 4)
            cand_copy["_contrib_skill"]            = round(contrib_skill, 4)
            cand_copy["_contrib_exp"]              = round(contrib_exp, 4)
            cand_copy["_contrib_act"]              = round(contrib_act, 4)
            # Matched / missed skill detail
            cand_copy["_matched_skills"]           = matched_skills
            cand_copy["_missed_skills"]            = missed_skills
            cand_copy["_skill_match_percent"]      = int(skill_ratio * 100)
            # Summary fields
            cand_copy["overall_score"]             = round(overall, 4)
            cand_copy["skills_match_percent"]      = cand_copy["_skill_match_percent"]
            cand_copy["semantic_similarity_percent"] = int(semantic_sim * 100)
            cand_copy["title_alignment_percent"]   = int(title_align * 100)
            ranked.append(cand_copy)
            t_aggregation += (time.perf_counter() - t0) * 1000

        # 6. Sorting Time
        t0 = time.perf_counter()
        # Sort: overall desc → role fit → skill fit → semantic → id (deterministic)
        ranked.sort(
            key=lambda x: (
                -x["overall_score"],
                -x["_title_alignment"],
                -x["_skill_overlap"],
                -x["_semantic_similarity"],
                x["candidate_id"],
            )
        )
        t_sorting += (time.perf_counter() - t0) * 1000
        total_ranking_ms = (time.perf_counter() - t_rank_start) * 1000
        self.last_timing_breakdown = {
            "Title Alignment Time": round(t_title_alignment, 2),
            "Skill Matching Time": round(t_skill_match, 2),
            "Alias Resolution Time": round(t_alias_resolution, 2),
            "Experience Scoring Time": round(t_experience, 2),
            "Semantic Score Calculation Time": round(t_semantic, 2),
            "Final Score Aggregation Time": round(t_aggregation, 2),
            "Sorting Time": round(t_sorting, 2),
            "Ranking Total Time": round(total_ranking_ms, 2),
        }

        logger.info(
            "RANKING TIMING - Title Alignment: %.2fms | Skill Match: %.2fms | Alias Resolution: %.2fms | Experience: %.2fms | Semantic: %.2fms | Aggregation: %.2fms | Sorting: %.2fms",
            t_title_alignment,
            t_skill_match,
            t_alias_resolution,
            t_experience,
            t_semantic,
            t_aggregation,
            t_sorting,
        )

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
