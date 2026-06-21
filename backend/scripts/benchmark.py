"""
benchmark.py
============
Script to run benchmarks for:
1. Index build time (for a sample of candidates, and extrapolated for full dataset).
2. Query latency (average of multiple jobs endpoint calls).
3. Memory usage (comparing memory before and after model/index initialization).
"""

import sys
import os
import time
import httpx
import numpy as np
import subprocess

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.ingestion.ingestion_service import IngestionService
from app.ml.embedding_model import CandidateEmbeddingModel, EMBEDDING_DIM
from app.ml.faiss_index import CandidateFaissIndex

def get_process_memory_mb():
    """Gets memory usage of current process in MB (Windows-compatible)."""
    pid = os.getpid()
    cmd = f"powershell -Command \"(Get-Process -Id {pid}).WorkingSet64 / 1024 / 1024\""
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        return round(float(output), 2)
    except Exception:
        return 0.0

def benchmark_indexing():
    print("=" * 65)
    print("1. Indexing Benchmark")
    print("=" * 65)
    
    mem_start = get_process_memory_mb()
    print(f"Initial process memory : {mem_start} MB")
    
    ingestion = IngestionService()
    t0 = time.time()
    # Load 200 candidates for sample indexing benchmarking
    candidates = ingestion.load_all_candidates(
        limit=200,
        validate=True,
        preprocess=True,
        exclude_honeypots=True,
        as_dict=True,
    )
    t1 = time.time()
    load_time = t1 - t0
    print(f"Loaded 200 candidates in: {load_time:.2f}s ({200/load_time:.1f} candidates/sec)")

    mem_after_load = get_process_memory_mb()
    print(f"Memory after loading candidates: {mem_after_load} MB (diff: {mem_after_load - mem_start:.2f} MB)")

    model = CandidateEmbeddingModel()
    texts = [model.build_candidate_search_string(c) for c in candidates]
    candidate_ids = [c["candidate_id"] for c in candidates]
    
    t2 = time.time()
    # This will load sentence-transformers model (first time downloads it)
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=False)
    t3 = time.time()
    encode_time = t3 - t2
    throughput = 200 / encode_time
    print(f"Encoded 200 candidates in: {encode_time:.2f}s ({throughput:.1f} candidates/sec)")

    mem_after_encode = get_process_memory_mb()
    print(f"Memory after loading model & encoding: {mem_after_encode} MB (diff: {mem_after_encode - mem_after_load:.2f} MB)")

    faiss_index = CandidateFaissIndex(dimension=EMBEDDING_DIM)
    t4 = time.time()
    faiss_index.add_vectors(embeddings, candidate_ids)
    t5 = time.time()
    index_time = t5 - t4
    print(f"FAISS index vectors added in: {index_time:.4f}s")
    
    mem_final = get_process_memory_mb()
    print(f"Final process memory   : {mem_final} MB (Total memory diff: {mem_final - mem_start:.2f} MB)")
    
    # Extrapolate for 20,000 candidates (the active dataset size)
    total_candidates = 20000
    extrapolated_encode_time_sec = total_candidates / throughput
    extrapolated_encode_time_min = extrapolated_encode_time_sec / 60.0
    print("-" * 65)
    print(f"Extrapolated metrics for full dataset ({total_candidates:,} candidates):")
    print(f"  Estimated Build/Encoding Time: {extrapolated_encode_time_min:.2f} minutes ({extrapolated_encode_time_sec:.1f} seconds)")
    print(f"  Estimated FAISS Index Size   : {(total_candidates * EMBEDDING_DIM * 4) / (1024 * 1024):.2f} MB")
    print("=" * 65)
    print()
    return {
        "throughput": throughput,
        "extrapolated_time_min": extrapolated_encode_time_min,
        "mem_diff_mb": mem_final - mem_start
    }

def benchmark_query_latency():
    print("=" * 65)
    print("2. Query Latency Benchmark")
    print("=" * 65)
    url = "http://127.0.0.1:8000/api/v1/jobs"
    payload = {
        "title": "Backend Engineer",
        "description": "Looking for Python engineer with FastAPI, FAISS, and ML experience.",
        "required_skills": ["Python", "FastAPI"],
        "top_k": 10
    }
    
    latencies = []
    # Warmup
    try:
        httpx.post(url, json=payload, timeout=15.0)
    except Exception as e:
        print(f"Warmup query failed: {e}. Is the server running on port 8000?")
        return
        
    for i in range(20):
        t0 = time.time()
        httpx.post(url, json=payload, timeout=15.0)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000) # in ms
        
    mean_lat = np.mean(latencies)
    median_lat = np.median(latencies)
    min_lat = np.min(latencies)
    max_lat = np.max(latencies)
    std_lat = np.std(latencies)
    print(f"Executed 20 search queries against FastAPI backend:")
    print(f"  Min latency    : {min_lat:.2f} ms")
    print(f"  Max latency    : {max_lat:.2f} ms")
    print(f"  Mean latency   : {mean_lat:.2f} ms")
    print(f"  Median latency : {median_lat:.2f} ms")
    print(f"  Std Dev latency: {std_lat:.2f} ms")
    print("=" * 65)
    print()
    return {
        "mean_ms": mean_lat,
        "median_ms": median_lat,
        "min_ms": min_lat,
        "max_ms": max_lat
    }

if __name__ == "__main__":
    benchmark_indexing()
    benchmark_query_latency()
