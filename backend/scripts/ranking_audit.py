#!/usr/bin/env python
"""
Ranking Audit Script
====================

Runs the full retrieval + ranking pipeline for a set of standard job titles
and produces a structured report with top-10 results, component scores,
and reasoning for each.

Usage::

    cd backend
    python scripts/ranking_audit.py

    # or with a custom title list:
    python scripts/ranking_audit.py "Backend Engineer" "ML Engineer"

This script loads the workspace in-process (no running server needed).
"""

import sys
import os
import time
import json
import logging

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_JOB_TITLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data Scientist",
    "ML Engineer",
    "DevOps Engineer",
]

# Skill sets for each title (used as required_skills input)
TITLE_SKILLS = {
    "Backend Engineer":    ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
    "Frontend Engineer":   ["React", "TypeScript", "JavaScript", "CSS", "Next.js"],
    "Full Stack Engineer": ["Python", "React", "TypeScript", "PostgreSQL", "Docker"],
    "Data Scientist":      ["Python", "Pandas", "Scikit-learn", "SQL", "Machine Learning"],
    "ML Engineer":         ["Python", "PyTorch", "TensorFlow", "Docker", "MLOps"],
    "DevOps Engineer":     ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD"],
}

DEFAULT_DESCRIPTION_TEMPLATE = (
    "We are looking for a {title} to join our team. "
    "The ideal candidate has strong experience in {skills_text}."
)


def run_audit(titles=None):
    """Load workspace and run audit for each title."""
    titles = titles or DEFAULT_JOB_TITLES

    print("=" * 70)
    print("RANKING AUDIT REPORT")
    print("=" * 70)
    print(f"Titles: {len(titles)}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Load workspace ───────────────────────────────────────────
    from app.api import deps
    from app.services.ranking.ranking_service import DEFAULT_WEIGHTS

    print("Loading workspace (cache + FAISS + model)...")
    t0 = time.perf_counter()

    retrieval = deps.get_retrieval_service()
    ingestion = deps.get_ingestion_service()
    retrieval.load_index_and_cache(ingestion)
    ranking = deps.get_ranking_service()
    explainability = deps.get_explainability_service()

    load_ms = (time.perf_counter() - t0) * 1000
    print(f"Workspace loaded in {load_ms:.0f}ms ({len(retrieval.candidates_cache):,} candidates)")
    print(f"Semantic mode: {retrieval.is_semantic_ready()}")
    print(f"Weights: {DEFAULT_WEIGHTS}")
    print()

    results = {}

    for title in titles:
        skills = TITLE_SKILLS.get(title, ["Python"])
        skills_text = ", ".join(skills)
        description = DEFAULT_DESCRIPTION_TEMPLATE.format(
            title=title, skills_text=skills_text
        )

        print("-" * 70)
        print(f"JOB TITLE: {title}")
        print(f"Skills: {skills_text}")
        print("-" * 70)

        t_start = time.perf_counter()

        # Retrieval
        candidates_with_scores, ret_timings = retrieval.retrieve_candidates(
            job_title=title,
            job_description=description,
            required_skills=skills,
            top_k=500,
            return_timings=True,
        )

        # Ranking
        ranked = ranking.hybrid_rank(
            required_skills=skills,
            candidates_with_scores=candidates_with_scores,
            top_k=100,
            job_title=title,
        )

        t_total = (time.perf_counter() - t_start) * 1000

        # Report top 10
        top_10 = ranked[:10]
        title_results = []

        print(f"\n{'Rank':<5} {'Overall':>8} {'Role':>6} {'Skill':>6} {'Sem':>6} {'Exp':>6} {'Act':>6}  {'Title':<35} {'Name'}")
        print("─" * 110)

        for i, cand in enumerate(top_10, 1):
            profile = cand.get("profile", {})
            name = profile.get("anonymized_name", "Unknown")
            cand_title = profile.get("current_title", "")
            overall = cand.get("overall_score", 0)
            role_pct = cand.get("title_alignment_percent", 0)
            skill_pct = cand.get("_skill_match_percent", 0)
            sem_pct = cand.get("semantic_similarity_percent", 0)
            exp = cand.get("_experience_match", 0)
            act = cand.get("_activity_score", 0)
            matched = cand.get("_matched_skills", [])
            missed = cand.get("_missed_skills", [])

            print(
                f"  {i:<3} {overall:>7.1%} {role_pct:>5}% {skill_pct:>5}% {sem_pct:>5}% "
                f"{exp:>5.2f} {act:>5.2f}  {cand_title[:35]:<35} {name}"
            )

            title_results.append({
                "rank": i,
                "name": name,
                "current_title": cand_title,
                "overall_score": round(overall, 4),
                "role_fit_percent": role_pct,
                "skill_match_percent": skill_pct,
                "semantic_percent": sem_pct,
                "experience_score": round(exp, 4),
                "activity_score": round(act, 4),
                "matched_skills": matched,
                "missed_skills": missed,
            })

        # Semantic distribution for this query
        if candidates_with_scores:
            scores = [s for _, s in candidates_with_scores]
            sem_min = min(scores)
            sem_avg = sum(scores) / len(scores)
            sem_max = max(scores)
            sem_top10 = sorted(scores, reverse=True)[:10]
            print(f"\n  Semantic Distribution: min={sem_min:.4f} avg={sem_avg:.4f} max={sem_max:.4f}")
            print(f"  Top 10 raw scores: {[round(s,4) for s in sem_top10]}")

        print(f"  Pipeline time: {t_total:.0f}ms")
        print()

        results[title] = {
            "candidates": title_results,
            "pipeline_ms": round(t_total, 2),
            "retrieval_pool": len(candidates_with_scores),
        }

    # Save JSON report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scratch",
        "ranking_audit_report.json",
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 70)
    print(f"Full report saved to: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    custom_titles = sys.argv[1:] if len(sys.argv) > 1 else None
    run_audit(custom_titles)
