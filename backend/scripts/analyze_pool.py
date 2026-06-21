"""Analyze title distribution in ranking pool."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from collections import Counter
from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import RankingService

ingestion = IngestionService()
retrieval = RetrievalService()
ranking   = RankingService()

retrieval.load_index_and_cache(ingestion)

req_skills = ["Python", "FastAPI", "Django", "REST API", "PostgreSQL", "Redis", "Docker", "Microservices", "SQL", "AWS"]
description = (
    "Looking for a Backend Engineer with strong Python experience. "
    "Must have expertise in building REST APIs, microservices, and "
    "working with databases (PostgreSQL, Redis). Experience with "
    "FastAPI or Django preferred."
)

cands_with_scores = retrieval.retrieve_candidates(
    job_title="Backend Engineer",
    job_description=description,
    required_skills=req_skills,
    top_k=500,
)

ranked = ranking.hybrid_rank(
    required_skills=req_skills,
    candidates_with_scores=cands_with_scores,
    top_k=500,
    job_title="Backend Engineer",
)

top100 = ranked[:100]
title_dist = Counter(c.get("profile", {}).get("current_title", "Unknown") for c in top100)
print("Title distribution in top-100:")
for t, cnt in title_dist.most_common(20):
    print(f"  {t:<40} {cnt}")

print()
print("Backend/Python/API Engineers in top-100:")
TARGET = {"backend", "python", "api engineer", "server-side", "server side"}
for i, c in enumerate(ranked[:100]):
    t = (c.get("profile", {}).get("current_title") or "").lower()
    if any(kw in t for kw in TARGET):
        cid = c["candidate_id"]
        ct  = (c["profile"]["current_title"] or "")[:40]
        fs  = c["overall_score"]
        ss  = c["_semantic_similarity"]
        ta  = c["_title_alignment"]
        so  = c["_skill_overlap"]
        print(f"  #{i+1:>3} {cid} {ct:<40} final={fs:.4f} sem={ss:.4f} title_aln={ta:.4f} skill={so:.4f}")
