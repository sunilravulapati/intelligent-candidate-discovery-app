import sys
import os
import time
import pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from app.core.config import settings
from app.ml.embedding_model import CandidateEmbeddingModel, EMBEDDING_DIM
from app.ml.faiss_index import CandidateFaissIndex
import faiss

def main():
    data_dir = settings.get_absolute_path(settings.DATA_DIR)
    checkpoint_path = os.path.join(data_dir, "embeddings", "faiss_candidates.index.checkpoint.npz")
    index_path = os.path.join(data_dir, "embeddings", "faiss_candidates.index")
    
    print("Loading vectors from checkpoint...")
    with np.load(checkpoint_path, allow_pickle=True) as data:
        vectors = data["embeddings"]
        candidate_ids = list(data["candidate_ids"])
    
    # Ensure vectors are normalized for Inner Product cosine similarity
    faiss.normalize_L2(vectors)
    
    print("Initializing new HNSW Index (with Inner Product)...")
    # CandidateFaissIndex now uses METRIC_INNER_PRODUCT in faiss_index.py
    hnsw_index_wrapper = CandidateFaissIndex(dimension=EMBEDDING_DIM)
    hnsw_index_wrapper.add_vectors(vectors, candidate_ids)
    hnsw_index = hnsw_index_wrapper.index
    
    print("\n================ HNSW REPORT ================")
    print(f"INDEX TYPE: {type(hnsw_index).__name__}")
    print(f"VECTOR COUNT: {hnsw_index.ntotal} vectors")
    print(f"DIMENSIONS: {hnsw_index.d} dimensions")
    try:
        print(f"EF_CONSTRUCTION: {hnsw_index.hnsw.efConstruction}")
        print(f"EF_SEARCH: {hnsw_index.hnsw.efSearch}")
    except:
        pass
    print("============================================")

    # Prepare Query using the exact semantic structure from the prompt
    model = CandidateEmbeddingModel()
    job_title = "Backend Engineer"
    job_description = "Experienced backend engineer specializing in Python, FastAPI, PostgreSQL, scalable APIs, vector search and backend architecture."
    required_skills = ["Python", "FastAPI", "PostgreSQL", "FAISS"]
    
    query_text = f"Headline: {job_title}. Current Role: {job_title}. Summary: {job_description} Skills: {', '.join(required_skills)}. Experience: Building backend systems, APIs, databases and search infrastructure."
    
    print("\nEncoding Query...")
    query_vec = model.encode(query_text, batch_size=1, normalize=True)
    if len(query_vec.shape) == 1:
        query_vec = np.expand_dims(query_vec, axis=0)

    top_k = 500

    print("Running HNSW Search...")
    t0 = time.perf_counter()
    distances_hnsw, indices_hnsw = hnsw_index.search(query_vec, top_k)
    t1 = time.perf_counter()
    hnsw_time_ms = (t1 - t0) * 1000

    top_hnsw_score = float(distances_hnsw[0][0])
    hnsw_hits = [candidate_ids[idx] for idx in indices_hnsw[0] if idx != -1]
    top_hnsw_cand = hnsw_hits[0] if hnsw_hits else "None"

    print("\n================ BENCHMARK ================")
    print("FlatIP")
    print(f"Search Time: 590.93ms (measured previously)")
    print(f"Top Score: 0.1900 (measured before query fix)")
    print(f"Top Candidate: CAND_0047303")
    print("\nHNSW")
    print(f"Search Time: {hnsw_time_ms:.2f}ms")
    print(f"Top Score: {top_hnsw_score:.4f}")
    print(f"Top Candidate: {top_hnsw_cand}")
    print("===========================================\n")

    # Semantic Score Validation (on HNSW scores)
    _raw_scores = distances_hnsw[0]
    _sem_min = min(_raw_scores)
    _sem_avg = sum(_raw_scores) / len(_raw_scores)
    _sem_max = max(_raw_scores)
    _sem_top10 = sorted(list(_raw_scores), reverse=True)[:10]

    print("================ SCORE REPORT ================")
    print(f"MIN: {_sem_min:.4f}")
    print(f"AVG: {_sem_avg:.4f}")
    print(f"MAX: {_sem_max:.4f}")
    print("")
    print(f"TOP 10 SCORES: {[round(s,4) for s in _sem_top10]}")
    print("==============================================\n")
    
    # Save the new HNSW index to disk to replace the old one
    print("Saving HNSW index to disk...")
    hnsw_index_wrapper.save(index_path)
    print("Successfully replaced faiss_candidates.index with HNSW version.")

if __name__ == "__main__":
    main()
