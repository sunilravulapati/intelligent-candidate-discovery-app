"""Inspect top candidates from submission to verify quality."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.ingestion.ingestion_service import IngestionService

ingestion = IngestionService()
candidates = ingestion.load_all_candidates(
    limit=-1, validate=True, preprocess=True, exclude_honeypots=True, as_dict=True
)
cand_map = {c["candidate_id"]: c for c in candidates}

top_ids = [
    "CAND_0000031", "CAND_0072660", "CAND_0062247",
    "CAND_0011162", "CAND_0041610", "CAND_0010685",
    "CAND_0006557", "CAND_0077337", "CAND_0065195", "CAND_0018549",
]

for cid in top_ids:
    c = cand_map.get(cid, {})
    p = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    skills = [s["name"] for s in c.get("skills", [])[:8]]
    title = p.get("current_title", "?")
    company = p.get("current_company", "?")
    years = p.get("years_of_experience", 0)
    industry = p.get("current_industry", "?")
    open_w = sig.get("open_to_work_flag", False)
    last_active = sig.get("last_active_date", "?")
    response = sig.get("recruiter_response_rate", 0)
    notice = sig.get("notice_period_days", "?")
    summary = p.get("summary", "")[:200]
    print(f"{cid}: {title} @ {company}")
    print(f"  Industry: {industry} | {years}yr experience")
    print(f"  Skills: {skills}")
    print(f"  Active: {open_w} | Last: {last_active} | Response: {response} | Notice: {notice}d")
    print(f"  Summary: {summary}...")
    print()
