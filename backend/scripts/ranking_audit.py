"""
ranking_audit.py  (v2)
======================
Comprehensive ranking audit with:
  - Per-component score breakdown (raw + weighted contribution)
  - Matched / missed skills per candidate
  - Old-vs-new weight comparison mode
  - Score dominance analysis (is semantic overpowering skill?)

Usage (from backend/ directory):
    # Standard audit with new weights
    .\\venv\\Scripts\\python scripts/ranking_audit.py --title "Backend Engineer"

    # Custom skills
    .\\venv\\Scripts\\python scripts/ranking_audit.py \\
        --title "Backend Engineer" \\
        --skills "Python,FastAPI,PostgreSQL,FAISS"

    # Old vs new weight comparison
    .\\venv\\Scripts\\python scripts/ranking_audit.py \\
        --title "Backend Engineer" --compare

Output sections:
  1. Component Contribution Audit  (weight × score for each component)
  2. Skill Detail Report           (matched / missed skills + overlap %)
  3. Score Dominance Analysis      (is semantic overpowering skill?)
  4. [Optional] Old vs New Ranking Comparison
"""

import sys
import os
import argparse
import logging
from collections import Counter
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import (
    RankingService,
    DEFAULT_WEIGHTS,
    OLD_WEIGHTS,
)

# ─────────────────────────────────────────────────────────────────────────────
# Built-in query presets
# ─────────────────────────────────────────────────────────────────────────────

PRESET_QUERIES: Dict[str, Dict] = {
    "backend engineer": {
        "description": (
            "Looking for a Backend Engineer with strong Python experience. "
            "Must have expertise in building REST APIs, microservices, and "
            "working with databases (PostgreSQL, Redis). Experience with "
            "FastAPI or Django preferred. Knowledge of cloud platforms and "
            "containerization (Docker, Kubernetes) is a plus."
        ),
        "required_skills": [
            "Python", "FastAPI", "PostgreSQL", "FAISS",
            "REST API", "Docker", "Microservices", "Redis",
        ],
    },
    "python developer": {
        "description": (
            "Python Developer with 3+ years of experience. Strong knowledge "
            "of Python frameworks, data structures, and backend development. "
            "Experience with web frameworks (Flask/FastAPI/Django), databases, "
            "and writing clean, testable code."
        ),
        "required_skills": [
            "Python", "Flask", "FastAPI", "Django", "SQL", "PostgreSQL",
            "REST API", "Git", "Docker",
        ],
    },
    "api engineer": {
        "description": (
            "API Engineer to design, build, and maintain scalable REST and "
            "GraphQL APIs. Must understand API design patterns, authentication, "
            "rate limiting, and documentation. Python or Node.js background."
        ),
        "required_skills": [
            "REST API", "GraphQL", "Python", "API design", "OAuth",
            "Swagger", "OpenAPI", "FastAPI", "Node.js",
        ],
    },
    "frontend engineer": {
        "description": (
            "Looking for a Frontend Engineer with strong React and TypeScript "
            "experience building polished web applications. Next.js, API "
            "integration, performance optimization, and testing experience preferred."
        ),
        "required_skills": [
            "React", "TypeScript", "JavaScript", "NextJS", "REST API",
            "Git", "Testing", "HTML", "CSS",
        ],
    },
    "ai engineer": {
        "description": (
            "AI Engineer to build applied machine learning and retrieval systems. "
            "Requires Python, embeddings, vector search, model evaluation, and "
            "production API experience."
        ),
        "required_skills": [
            "Python", "Pytorch", "HuggingFace", "Embeddings", "Vector Search",
            "FAISS", "NLP", "Evaluation", "FastAPI",
        ],
    },
    "data scientist": {
        "description": (
            "Data Scientist with strong statistical analysis, machine learning, "
            "Python, SQL, experimentation, and model evaluation experience."
        ),
        "required_skills": [
            "Python", "SQL", "Pandas", "Numpy", "Scikit-learn",
            "Machine Learning", "Evaluation", "Spark",
        ],
    },
    "devops engineer": {
        "description": (
            "DevOps Engineer to own cloud infrastructure, CI/CD, containers, "
            "Kubernetes operations, monitoring, and production reliability."
        ),
        "required_skills": [
            "AWS", "Docker", "Kubernetes", "Terraform", "CI/CD",
            "Linux", "Prometheus", "Grafana",
        ],
    },
    "full stack engineer": {
        "description": (
            "Full Stack Engineer with frontend and backend experience across React, "
            "TypeScript, APIs, databases, cloud deployment, and production ownership."
        ),
        "required_skills": [
            "React", "TypeScript", "Python", "Node.js", "REST API",
            "PostgreSQL", "AWS", "Docker",
        ],
    },
}


def _get_preset(title: str) -> Dict:
    key = title.lower().strip()
    return PRESET_QUERIES.get(key, {
        "description": f"Looking for a {title} with relevant experience.",
        "required_skills": [],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

SEP = "─" * 110
THICK = "═" * 110


def _fmt_skills(skills: List[str], max_skills: int = 5) -> str:
    if not skills:
        return "—"
    shown = skills[:max_skills]
    rest  = len(skills) - max_skills
    s = ", ".join(shown)
    if rest > 0:
        s += f" (+{rest} more)"
    return s


def _bar(value: float, width: int = 12) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def _pct(value: float) -> str:
    return f"{value * 100:5.1f}%"


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: Component contribution audit
# ─────────────────────────────────────────────────────────────────────────────

def print_contribution_audit(ranked: List[Dict], top_k: int, weights: Dict, label: str = "") -> None:
    w = weights
    tag = f" [{label}]" if label else ""

    print(f"\n{THICK}")
    print(f"  SECTION 1 — Component Contribution Audit{tag}  (top {top_k})")
    print(f"  Weights: semantic={w['semantic_similarity']:.2f}  "
          f"title={w['title_alignment']:.2f}  "
          f"skill={w['skill_overlap']:.2f}  "
          f"exp={w['experience_match']:.2f}  "
          f"act={w['activity_score']:.2f}")
    print(THICK)

    HDR = (
        f"{'#':>3} "
        f"{'ID':<14} "
        f"{'Current Title':<32} "
        f"{'SEM raw→wt':>14} "
        f"{'TITLE raw→wt':>14} "
        f"{'SKILL raw→wt':>14} "
        f"{'EXP raw→wt':>12} "
        f"{'ACT raw→wt':>12} "
        f"{'FINAL':>8}"
    )
    print(HDR)
    print(SEP)

    for i, c in enumerate(ranked[:top_k], 1):
        profile   = c.get("profile", {})
        title     = (profile.get("current_title") or "—")[:32]
        cand_id   = c.get("candidate_id", "?")

        sem_r = c.get("_semantic_similarity", 0.0)
        tit_r = c.get("_title_alignment",     0.0)
        skl_r = c.get("_skill_match_percent",  0) / 100.0
        exp_r = c.get("_experience_match",     0.0)
        act_r = c.get("_activity_score",       0.0)

        sem_w = c.get("_contrib_semantic", 0.0)
        tit_w = c.get("_contrib_title",    0.0)
        skl_w = c.get("_contrib_skill",    0.0)
        exp_w = c.get("_contrib_exp",      0.0)
        act_w = c.get("_contrib_act",      0.0)

        final = c.get("overall_score", 0.0)

        print(
            f"{i:>3} "
            f"{cand_id:<14} "
            f"{title:<32} "
            f"{sem_r:.3f}→{sem_w:.3f}  "
            f"{tit_r:.3f}→{tit_w:.3f}  "
            f"{skl_r:.3f}→{skl_w:.3f}  "
            f"{exp_r:.3f}→{exp_w:.3f}  "
            f"{act_r:.3f}→{act_w:.3f}  "
            f"{final:.4f}"
        )

    print(SEP)

    # Dominance analysis
    sems  = [c.get("_contrib_semantic", 0.0) for c in ranked[:top_k]]
    skills = [c.get("_contrib_skill",   0.0) for c in ranked[:top_k]]
    titles = [c.get("_contrib_title",   0.0) for c in ranked[:top_k]]

    avg_sem   = sum(sems)   / len(sems)   if sems   else 0.0
    avg_skill = sum(skills) / len(skills) if skills else 0.0
    avg_title = sum(titles) / len(titles) if titles else 0.0

    print(f"\n  Average weighted contribution (top-{top_k}):")
    print(f"    semantic  : {avg_sem:.4f}  {_bar(avg_sem/0.35 if avg_sem else 0)}")
    print(f"    title_aln : {avg_title:.4f}  {_bar(avg_title/0.20 if avg_title else 0)}")
    print(f"    skill_ovlp: {avg_skill:.4f}  {_bar(avg_skill/0.30 if avg_skill else 0)}")

    if avg_sem > 0 and avg_skill > 0:
        ratio = avg_sem / avg_skill
        flag = "⚠️  SEMANTIC IS DOMINATING" if ratio > 2.5 else "✅ Balanced"
        print(f"\n  Semantic/Skill contribution ratio: {ratio:.2f}x  {flag}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: Skill detail report
# ─────────────────────────────────────────────────────────────────────────────

def print_skill_report(ranked: List[Dict], required_skills: List[str], top_k: int) -> None:
    print(f"\n{THICK}")
    print(f"  SECTION 2 — Skill Detail Report  (top {top_k})")
    print(f"  Required: {required_skills}")
    print(THICK)

    HDR = (
        f"{'#':>3} "
        f"{'ID':<14} "
        f"{'Title':<30} "
        f"{'Ovlp':>5} "
        f"{'Matched Skills':<40} "
        f"{'Missed Skills':<40} "
        f"{'Score':>7}"
    )
    print(HDR)
    print(SEP)

    for i, c in enumerate(ranked[:top_k], 1):
        profile  = c.get("profile", {})
        title    = (profile.get("current_title") or "—")[:30]
        cand_id  = c.get("candidate_id", "?")
        ovlp     = c.get("_skill_match_percent", 0) / 100.0
        matched  = c.get("_matched_skills", [])
        missed   = c.get("_missed_skills",  [])
        final    = c.get("overall_score", 0.0)

        matched_str = _fmt_skills(matched, 4)[:40]
        missed_str  = _fmt_skills(missed,  4)[:40]

        ovlp_flag = "🔴" if ovlp < 0.25 else ("🟡" if ovlp < 0.50 else "🟢")
        print(
            f"{i:>3} "
            f"{cand_id:<14} "
            f"{title:<30} "
            f"{ovlp_flag}{_pct(ovlp)} "
            f"{matched_str:<40} "
            f"{missed_str:<40} "
            f"{final:>7.4f}"
        )

    print(SEP)

    # Skill coverage summary
    all_matched = [sk for c in ranked[:top_k] for sk in c.get("_matched_skills", [])]
    skill_freq  = Counter(all_matched)
    print(f"\n  Skill coverage in top-{top_k} candidates:")
    for sk in required_skills:
        cnt  = skill_freq.get(sk, 0)
        pct  = cnt / top_k * 100
        bar  = "█" * cnt + "░" * (top_k - cnt)
        flag = "⚠️" if pct < 30 else ("🟡" if pct < 60 else "✅")
        print(f"    {flag} {sk:<25} {cnt:>3}/{top_k}  ({pct:5.1f}%)  {bar[:top_k]}")

    # Low overlap alert
    low_overlap = [c for c in ranked[:top_k] if (c.get("_skill_match_percent", 0) / 100.0) < 0.25]
    if low_overlap:
        print(f"\n  ⚠️  {len(low_overlap)} candidate(s) in top-{top_k} have <25% skill overlap:")
        for c in low_overlap:
            pid   = c.get("candidate_id", "?")
            title = (c.get("profile", {}).get("current_title") or "?")[:40]
            ovlp  = c.get("_skill_match_percent", 0) / 100.0
            sem   = c.get("_semantic_similarity", 0.0)
            print(f"    {pid}  {title:<40}  overlap={_pct(ovlp)}  semantic={sem:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: Score dominance analysis
# ─────────────────────────────────────────────────────────────────────────────

def print_dominance_analysis(
    ranked: List[Dict],
    top_k: int,
    weights: Dict,
) -> None:
    print(f"\n{THICK}")
    print(f"  SECTION 3 — Score Dominance Analysis  (top {top_k})")
    print(THICK)

    # Compute correlation proxy: does high semantic = low skill overlap?
    pairs = [
        (c.get("_semantic_similarity", 0.0), c.get("_skill_match_percent", 0) / 100.0)
        for c in ranked[:top_k]
    ]
    sem_vals  = [p[0] for p in pairs]
    skill_vals = [p[1] for p in pairs]

    n = len(pairs)
    if n < 2:
        print("  Not enough data for analysis.")
        return

    avg_sem   = sum(sem_vals) / n
    avg_skill = sum(skill_vals) / n

    # Max possible contribution from each component
    max_sem_contrib   = weights["semantic_similarity"] * 1.0
    max_skill_contrib = weights["skill_overlap"]       * 1.0
    max_title_contrib = weights["title_alignment"]     * 1.0

    print(f"\n  Max achievable contribution per component:")
    print(f"    semantic_similarity : {max_sem_contrib:.4f}  (weight={weights['semantic_similarity']:.2f})")
    print(f"    title_alignment     : {max_title_contrib:.4f}  (weight={weights['title_alignment']:.2f})")
    print(f"    skill_overlap       : {max_skill_contrib:.4f}  (weight={weights['skill_overlap']:.2f})")

    print(f"\n  Observed averages in top-{top_k}:")
    print(f"    semantic score    : {avg_sem:.4f}   → weighted contribution avg: {avg_sem * weights['semantic_similarity']:.4f}")
    print(f"    skill overlap     : {avg_skill:.4f}   → weighted contribution avg: {avg_skill * weights['skill_overlap']:.4f}")

    # How many candidates beat the semantic floor with skill alone?
    sem_floor = avg_sem * weights["semantic_similarity"]
    dominated_by_sem = sum(
        1 for c in ranked[:top_k]
        if c.get("_contrib_semantic", 0.0) > c.get("_contrib_skill", 0.0) * 2
    )
    print(f"\n  Candidates where semantic contribution > 2× skill contribution: "
          f"{dominated_by_sem}/{top_k}  "
          f"({'⚠️ high' if dominated_by_sem > top_k * 0.5 else '✅ ok'})")

    # Skill threshold table
    thresholds = [0.0, 0.25, 0.50, 0.75, 1.0]
    print(f"\n  Skill overlap distribution in top-{top_k}:")
    prev = 0.0
    for thr in thresholds[1:]:
        cnt = sum(1 for c in ranked[:top_k]
                  if prev <= (c.get("_skill_match_percent", 0) / 100.0) < thr)
        bar = "█" * cnt
        print(f"    [{prev:.0%} – {thr:.0%}): {cnt:>3}  {bar}")
        prev = thr
    cnt = sum(1 for c in ranked[:top_k] if c.get("_skill_match_percent", 0) >= 100)
    print(f"    [100%]           : {cnt:>3}  {'█' * cnt}")

    print(f"\n  Semantic score range in top-{top_k}:")
    print(f"    min={min(sem_vals):.4f}  avg={avg_sem:.4f}  max={max(sem_vals):.4f}")
    sem_spread = max(sem_vals) - min(sem_vals)
    print(f"    spread={sem_spread:.4f}  "
          f"({'⚠️  NARROW — semantic is a weak discriminator' if sem_spread < 0.05 else '✅ adequate spread'})")


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: Old vs new comparison
# ─────────────────────────────────────────────────────────────────────────────

def print_weight_comparison(
    ranked_old: List[Dict],
    ranked_new: List[Dict],
    top_k: int,
) -> None:
    print(f"\n{THICK}")
    print(f"  SECTION 4 — Old vs New Weights Comparison  (top {top_k})")
    print(f"  OLD: semantic=0.40  title=0.20  skill=0.20  exp=0.10  act=0.10")
    print(f"  NEW: semantic=0.35  title=0.20  skill=0.30  exp=0.10  act=0.05")
    print(THICK)

    old_ids  = [c.get("candidate_id") for c in ranked_old[:top_k]]
    new_ids  = [c.get("candidate_id") for c in ranked_new[:top_k]]
    old_map  = {c["candidate_id"]: c for c in ranked_old[:top_k]}
    new_map  = {c["candidate_id"]: c for c in ranked_new[:top_k]}
    all_ids  = list(dict.fromkeys(old_ids + new_ids))  # preserve order, deduplicate

    HDR = (
        f"{'ID':<14} "
        f"{'Title':<30} "
        f"{'Skill%':>6} "
        f"{'OldRnk':>6} "
        f"{'OldScr':>7} "
        f"{'NewRnk':>6} "
        f"{'NewScr':>7} "
        f"{'Δrank':>6} "
        f"{'Δscore':>7} "
        f"{'Movement'}"
    )
    print(HDR)
    print(SEP)

    for cid in all_ids:
        old_c = old_map.get(cid)
        new_c = new_map.get(cid)
        ref   = new_c or old_c
        profile = ref.get("profile", {}) if ref else {}
        title   = (profile.get("current_title") or "—")[:30]
        skill_pct = (new_c or old_c or {}).get("_skill_match_percent", 0) / 100.0

        old_rank  = old_ids.index(cid) + 1 if cid in old_ids else "—"
        new_rank  = new_ids.index(cid) + 1 if cid in new_ids else "—"
        old_score = old_c.get("overall_score", 0.0) if old_c else 0.0
        new_score = new_c.get("overall_score", 0.0) if new_c else 0.0

        if isinstance(old_rank, int) and isinstance(new_rank, int):
            delta_rank  = old_rank - new_rank  # positive = moved up
            delta_score = new_score - old_score
            if   delta_rank > 2:  movement = f"⬆️  +{delta_rank}"
            elif delta_rank < -2: movement = f"⬇️  {delta_rank}"
            else:                 movement = f"➡️  {delta_rank:+d}"
        elif old_rank == "—":
            delta_rank  = "NEW"
            delta_score = new_score
            movement    = "🆕 entered top-k"
        else:
            delta_rank  = "OUT"
            delta_score = -old_score
            movement    = "❌ dropped out"

        skill_flag = "🔴" if skill_pct < 0.25 else ("🟡" if skill_pct < 0.50 else "🟢")

        print(
            f"{cid:<14} "
            f"{title:<30} "
            f"{skill_flag}{_pct(skill_pct)} "
            f"{str(old_rank):>6} "
            f"{old_score:>7.4f} "
            f"{str(new_rank):>6} "
            f"{new_score:>7.4f} "
            f"{str(delta_rank):>6} "
            f"{(delta_score):>+7.4f} "
            f"{movement}"
        )

    print(SEP)

    # Summary
    entered = [cid for cid in new_ids if cid not in old_ids]
    dropped = [cid for cid in old_ids if cid not in new_ids]

    print(f"\n  New entrants to top-{top_k}: {len(entered)}")
    for cid in entered[:5]:
        c = new_map.get(cid, {})
        title = (c.get("profile", {}).get("current_title") or "?")[:40]
        skill = c.get("_skill_match_percent", 0) / 100.0
        print(f"    + {cid}  {title:<40}  skill={_pct(skill)}")

    print(f"\n  Dropped from top-{top_k}: {len(dropped)}")
    for cid in dropped[:5]:
        c = old_map.get(cid, {})
        title = (c.get("profile", {}).get("current_title") or "?")[:40]
        skill = c.get("_skill_match_percent", 0) / 100.0
        print(f"    - {cid}  {title:<40}  skill={_pct(skill)}")

    # Avg skill overlap comparison
    avg_skill_old = sum(c.get("_skill_match_percent", 0) / 100.0 for c in ranked_old[:top_k]) / top_k
    avg_skill_new = sum(c.get("_skill_match_percent", 0) / 100.0 for c in ranked_new[:top_k]) / top_k
    print(f"\n  Avg skill overlap in top-{top_k}:")
    print(f"    Old weights: {_pct(avg_skill_old)}  New weights: {_pct(avg_skill_new)}  "
          f"Δ={_pct(avg_skill_new - avg_skill_old)}")
    if avg_skill_new > avg_skill_old:
        print(f"  ✅ New weights produced higher average skill overlap")
    else:
        print(f"  ⚠️  Skill overlap did not improve (dataset may lack high-skill candidates)")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive ranking audit with component breakdown and weight comparison.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--title",    "-t", type=str, default="Backend Engineer",
                        help="Job title to search (default: 'Backend Engineer').")
    parser.add_argument("--description", "-d", type=str, default="",
                        help="Optional job description override.")
    parser.add_argument("--skills",   "-s", type=str, default="",
                        help="Comma-separated required skills override.")
    parser.add_argument("--top-k",   "-k", type=int, default=20,
                        help="Candidates shown per section (default: 20).")
    parser.add_argument("--retrieve",      type=int, default=500,
                        help="FAISS retrieval pool size (default: 500).")
    parser.add_argument("--compare",  "-c", action="store_true",
                        help="Also rank with old weights and show comparison.")
    parser.add_argument("--section",       type=int, default=0,
                        help="Print only section N (1-4). 0 = all sections.")
    args = parser.parse_args()

    preset = _get_preset(args.title)
    description     = args.description or preset["description"]
    required_skills = (
        [s.strip() for s in args.skills.split(",") if s.strip()]
        if args.skills else preset["required_skills"]
    )

    print(f"\n{'█' * 80}")
    print(f"  RANKING AUDIT  v2")
    print(f"  Job title   : '{args.title}'")
    print(f"  Required    : {required_skills}")
    print(f"  Weights     : semantic={DEFAULT_WEIGHTS['semantic_similarity']:.2f}  "
          f"title={DEFAULT_WEIGHTS['title_alignment']:.2f}  "
          f"skill={DEFAULT_WEIGHTS['skill_overlap']:.2f}  "
          f"exp={DEFAULT_WEIGHTS['experience_match']:.2f}  "
          f"act={DEFAULT_WEIGHTS['activity_score']:.2f}")
    print(f"{'█' * 80}")

    # Load services
    ingestion = IngestionService()
    retrieval = RetrievalService()
    ranking   = RankingService()

    print("\nLoading candidate cache + FAISS index...")
    retrieval.load_index_and_cache(ingestion)

    mode = "SEMANTIC" if retrieval.is_semantic_ready() else "KEYWORD"
    print(f"Mode: {mode}  |  Candidates: {len(retrieval.candidates_cache):,}")
    if retrieval.is_semantic_ready():
        print(f"FAISS vectors: {retrieval._faiss.ntotal:,}")

    # Retrieve
    print(f"\nRetrieving top-{args.retrieve} via FAISS...")
    pool = retrieval.retrieve_candidates(
        job_title=args.title,
        job_description=description,
        required_skills=required_skills,
        top_k=args.retrieve,
    )
    print(f"Retrieved: {len(pool)} candidates")

    # Rank with new weights (default)
    print(f"\nRanking with new weights (semantic=0.35, skill=0.30)...")
    ranked_new = ranking.hybrid_rank(
        required_skills=required_skills,
        candidates_with_scores=pool,
        weights=DEFAULT_WEIGHTS,
        top_k=args.top_k,
        job_title=args.title,
    )

    # Rank with old weights (for comparison)
    ranked_old: Optional[List] = None
    if args.compare:
        print("Ranking with old weights (semantic=0.40, skill=0.20) for comparison...")
        ranked_old = ranking.hybrid_rank(
            required_skills=required_skills,
            candidates_with_scores=pool,
            weights=OLD_WEIGHTS,
            top_k=args.top_k,
            job_title=args.title,
        )

    # Print sections
    show_all = (args.section == 0)

    if show_all or args.section == 1:
        print_contribution_audit(ranked_new, args.top_k, DEFAULT_WEIGHTS, "NEW")

    if show_all or args.section == 2:
        print_skill_report(ranked_new, required_skills, args.top_k)

    if show_all or args.section == 3:
        print_dominance_analysis(ranked_new, args.top_k, DEFAULT_WEIGHTS)

    if (show_all or args.section == 4) and ranked_old is not None:
        print_weight_comparison(ranked_old, ranked_new, args.top_k)
    elif args.section == 4 and ranked_old is None:
        print("\n⚠️  Section 4 requires --compare flag.")

    print(f"\n{'█' * 80}\n")


if __name__ == "__main__":
    main()
