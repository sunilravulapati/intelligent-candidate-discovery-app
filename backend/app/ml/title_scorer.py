"""
title_scorer.py
===============
Normalized title alignment scoring for candidate-to-job title matching.

Algorithm
---------
The final score is a linear blend of three signals:

  1. Token Jaccard similarity  – word-level overlap between job title and
                                  candidate title (catches word reuse).
  2. Semantic category match   – role family lookup via a curated synonym
                                  map (e.g. "backend" family includes
                                  "api engineer", "server-side engineer").
  3. Seniority alignment       – optional bonus when seniority keywords
                                  (senior/lead/staff/principal) match.

The three signals are blended with fixed internal weights and the result
is clamped to [0.0, 1.0].
"""

import re
from typing import Dict, List, Optional, Set, Tuple


# ── Seniority tiers ────────────────────────────────────────────────────────────

_SENIORITY_TIERS: List[Set[str]] = [
    # junior
    {"intern", "trainee", "associate", "junior", "jr", "graduate", "entry"},
    # mid
    {"engineer", "developer", "programmer", "analyst", "consultant"},
    # senior / lead
    {"senior", "sr", "lead", "staff", "principal", "expert"},
    # management
    {"manager", "director", "head", "vp", "cto", "architect", "chief"},
]


def _seniority_tier(tokens: Set[str]) -> int:
    """Return seniority tier index (0=junior … 3=management). -1 if ambiguous."""
    for i, tier in enumerate(_SENIORITY_TIERS):
        if tokens & tier:
            return i
    return -1


# ── Role-family synonym map ───────────────────────────────────────────────────
# Keys = canonical family name; values = sets of phrases / tokens that belong
# to that family.  Phrases are lowercased and stripped.

_ROLE_FAMILIES: Dict[str, Set[str]] = {
    "backend": {
        "backend", "back end", "back-end", "server side", "server-side",
        "backend systems", "systems engineer", "backend systems engineer",
        "api", "api developer", "api engineer", "node", "django", "flask",
        "fastapi", "spring boot", "rails", "ruby on rails",
        "microservices", "rest api", "graphql", "grpc",
    },
    "frontend": {
        "frontend", "front end", "front-end", "ui", "ux", "react",
        "angular", "vue", "svelte", "next.js", "nuxt", "web developer",
        "web engineer", "ui developer", "ui engineer",
    },
    "fullstack": {
        "full stack", "fullstack", "full-stack",
        "generalist engineer", "generalist developer",
    },
    "cloud": {
        "cloud", "cloud engineer", "cloud architect", "devops", "dev ops",
        "sre", "site reliability", "platform engineer", "platform developer",
        "infrastructure", "infra", "aws", "azure", "gcp",
        "kubernetes", "k8s", "terraform", "ansible",
    },
    "data": {
        "data engineer", "data engineering", "etl", "pipeline",
        "data platform", "bigdata", "big data", "spark", "hadoop",
        "data warehouse", "datawarehouse", "dbt",
    },
    "ml": {
        "machine learning", "ml engineer", "ai engineer", "ai/ml",
        "nlp", "nlp engineer", "deep learning", "research engineer",
        "applied scientist", "data scientist", "computer vision",
        "recommendation", "ranking engineer", "search engineer",
        "llm", "llm engineer", "generative ai", "genai",
    },
    "mobile": {
        "android", "ios", "mobile", "flutter", "react native",
        "swift", "kotlin", "objective-c",
    },
    "embedded": {
        "embedded", "firmware", "iot", "rtos", "fpga", "hardware",
    },
    "security": {
        "security", "cybersecurity", "cyber security", "infosec",
        "appsec", "penetration", "pentest",
    },
    "qa": {
        "qa", "quality assurance", "test engineer", "sdet",
        "automation engineer", "testing",
    },
    "python": {
        "python developer", "python engineer", "python programmer",
        "pythonista",
    },
}

# ── Derived: phrase → family mapping (for fast lookup) ────────────────────────

def _build_phrase_to_family() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for family, phrases in _ROLE_FAMILIES.items():
        for phrase in phrases:
            mapping[phrase.lower().strip()] = family
    return mapping


_PHRASE_TO_FAMILY: Dict[str, str] = _build_phrase_to_family()

# Sorted by descending phrase length so longer matches win first
_FAMILY_PHRASES_SORTED: List[str] = sorted(
    _PHRASE_TO_FAMILY.keys(), key=len, reverse=True
)

# Backend-adjacent families: a "Backend Engineer" query should also reward
# these if the candidate has them (partial credit).
_BACKEND_ADJACENT: Set[str] = {"python", "fullstack", "ml"}
_FULLSTACK_ADJACENT: Set[str] = {"backend", "frontend", "python"}


def _adjacent_families(family: str) -> Set[str]:
    """Return families that are partially aligned with the given family."""
    _MAP: Dict[str, Set[str]] = {
        "backend":   _BACKEND_ADJACENT,
        "fullstack": _FULLSTACK_ADJACENT,
        "python":    {"backend", "fullstack", "ml"},
        "ml":        {"backend", "data", "python"},
        "cloud":     set(),  # cloud is NOT adjacent to backend
        "data":      {"ml"},
        "frontend":  {"fullstack"},
    }
    return _MAP.get(family, set())


# ── Helpers ────────────────────────────────────────────────────────────────────

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> Set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _family_of(title: str) -> Optional[str]:
    """
    Return the role family of a title by scanning for longest matching phrase.
    Returns None if no match is found.
    """
    t = title.lower().strip()
    for phrase in _FAMILY_PHRASES_SORTED:
        if phrase in t:
            return _PHRASE_TO_FAMILY[phrase]
    return None


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


# ── Public scorer ─────────────────────────────────────────────────────────────


class TitleAlignmentScorer:
    """
    Scores how well a candidate's current title aligns with a requested job
    title.  Returns a float in [0.0, 1.0].

    Usage::

        scorer = TitleAlignmentScorer()
        score = scorer.score("Backend Engineer", "API Developer")   # → ~0.80
        score = scorer.score("Backend Engineer", "Cloud Engineer")  # → ~0.15
    """

    # Internal blend weights (must sum to 1.0)
    _W_JACCARD:   float = 0.25
    _W_FAMILY:    float = 0.65
    _W_SENIORITY: float = 0.10

    def score(self, job_title: str, candidate_title: str) -> float:
        """
        Compute a normalized [0, 1] alignment score.

        Args:
            job_title:       The requested role title (from the search query).
            candidate_title: The candidate's current_title field.

        Returns:
            float in [0.0, 1.0].
        """
        if not job_title or not candidate_title:
            return 0.0

        job_tok = _tokenize(job_title)
        cand_tok = _tokenize(candidate_title)

        # ── Signal 1: token Jaccard ─────────────────────────────────────────
        jaccard = _jaccard(job_tok, cand_tok)

        # ── Signal 2: role-family category match ────────────────────────────
        job_family  = _family_of(job_title)
        cand_family = _family_of(candidate_title)

        if job_family is None or cand_family is None:
            # Cannot determine family — fall back to Jaccard only
            family_score = jaccard
        elif job_family == cand_family:
            family_score = 1.0
        elif cand_family in _adjacent_families(job_family):
            # Partial credit for adjacent families
            family_score = 0.55
        else:
            # Conflicting role families — penalise shared generic tokens (e.g. "engineer")
            family_score = 0.0
            jaccard = min(jaccard, 0.15)

        # ── Signal 3: seniority tier alignment ──────────────────────────────
        job_tier  = _seniority_tier(job_tok)
        cand_tier = _seniority_tier(cand_tok)

        if job_tier == -1 or cand_tier == -1:
            seniority_score = 0.5  # unknown → neutral
        elif job_tier == cand_tier:
            seniority_score = 1.0
        elif abs(job_tier - cand_tier) == 1:
            seniority_score = 0.5
        else:
            seniority_score = 0.0

        # ── Blend ────────────────────────────────────────────────────────────
        raw = (
            self._W_JACCARD   * jaccard
            + self._W_FAMILY    * family_score
            + self._W_SENIORITY * seniority_score
        )
        return round(min(max(raw, 0.0), 1.0), 4)

    def score_candidate(
        self, job_title: str, candidate: Dict
    ) -> Tuple[float, str]:
        """
        Convenience wrapper that extracts current_title from a candidate dict.

        Returns:
            (score, candidate_current_title)
        """
        cand_title: str = (
            candidate.get("profile", {}).get("current_title", "") or ""
        )
        return self.score(job_title, cand_title), cand_title


# Module-level singleton
_scorer = TitleAlignmentScorer()


def score_title_alignment(job_title: str, candidate: Dict) -> float:
    """
    Module-level convenience function.  Returns [0, 1] title alignment score.
    """
    score, _ = _scorer.score_candidate(job_title, candidate)
    return score
