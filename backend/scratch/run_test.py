import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force utf-8 stdout to avoid charmmap encoding errors
sys.stdout.reconfigure(encoding='utf-8')

from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retrieval_service import RetrievalService
from app.api.v1.endpoints.jobs import _tokenize

def main():
    ingestion = IngestionService()
    retrieval = RetrievalService()

    print("=== First Load ===")
    retrieval.load_index_and_cache(ingestion)

    print("\n=== Search ===")
    job_title = "Backend Engineer"
    job_description = "Looking for Python engineer with FastAPI, FAISS, and ML experience."
    required_skills = ["Python", "FastAPI"]
    
    # We will simulate exactly what jobs.py does, including the cProfile
    import time
    import cProfile, pstats, io
    
    t_retrieval_call_start = time.perf_counter()
    pr = cProfile.Profile()
    pr.enable()
    
    results, timings = retrieval.retrieve_candidates(
        job_title=job_title,
        job_description=job_description,
        required_skills=required_skills,
        top_k=500,
        return_timings=True
    )
    
    pr.disable()
    t_retrieval_call_end = time.perf_counter()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(30)
    print("\n==================================================")
    print("TOP TIME CONSUMERS")
    print("==================")
    print(s.getvalue())
    print("==================================================\n")
    
    retrieval_timer_ms = (t_retrieval_call_end - t_retrieval_call_start) * 1000
    print(f"RETRIEVAL_TIMER = {retrieval_timer_ms:.2f}ms")
    print(f"FAISS_TIMER = {timings.get('FAISS Retrieval', 0.0):.2f}ms")
    
if __name__ == "__main__":
    main()
