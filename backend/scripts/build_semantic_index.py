"""
build_semantic_index.py
=======================
Offline CLI script to build the FAISS semantic index from the challenge candidate dataset.

Run once before starting the API server:

    cd backend
    .\\venv\\Scripts\\python scripts/build_semantic_index.py

Or with a limit for quick testing:

    .\\venv\\Scripts\\python scripts/build_semantic_index.py --limit 1000

Artifacts produced:
    data/embeddings/faiss_candidates.index
    data/embeddings/faiss_candidates.index.meta
"""

import sys
import os
import time
import argparse
import logging
import pickle

import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.ingestion.ingestion_service import IngestionService
from app.ml.embedding_model import CandidateEmbeddingModel, EMBEDDING_DIM
from app.ml.faiss_index import CandidateFaissIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build FAISS semantic index from challenge candidate dataset."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=-1,
        help="Max candidates to embed (default: all). Use --limit 1000 for a quick test.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Sentence-transformer encoding batch size (default: 64).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for index files. Defaults to data/embeddings/ resolved from config.",
    )
    parser.add_argument(
        "--index-name",
        type=str,
        default="faiss_candidates.index",
        help="File name for the FAISS index (default: faiss_candidates.index).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve output directory
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        data_dir = settings.get_absolute_path(settings.DATA_DIR)
        output_dir = os.path.join(data_dir, "embeddings")

    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, args.index_name)

    logger.info("=" * 60)
    logger.info("Redrob Semantic Index Builder")
    logger.info(f"  Output: {index_path}")
    logger.info(f"  Batch size: {args.batch_size}")
    logger.info(f"  Limit: {'all' if args.limit < 0 else args.limit}")
    logger.info("=" * 60)

    # ── Step 1: Stream candidates ─────────────────────────────────
    t0 = time.time()
    logger.info("Step 1/4: Streaming candidates from dataset (honeypots excluded)...")

    ingestion = IngestionService()
    status = ingestion.get_candidate_files_status()
    active = status.get("active_source")
    if not active:
        logger.error("No candidate dataset files found. Aborting.")
        sys.exit(1)

    logger.info(f"  Source: {status[active]['path']} ({status[active]['size_mb']} MB)")

    candidates = ingestion.load_all_candidates(
        limit=args.limit,
        validate=True,
        preprocess=True,
        exclude_honeypots=True,
        as_dict=True,
    )

    n_candidates = len(candidates)
    if n_candidates == 0:
        logger.error("No candidates loaded. Aborting.")
        sys.exit(1)

    t1 = time.time()
    logger.info(f"  Loaded {n_candidates:,} candidates in {t1 - t0:.1f}s")

    # ── Step 2: Build composite texts ─────────────────────────────
    logger.info("Step 2/4: Building candidate composite texts...")
    model = CandidateEmbeddingModel()
    texts = [model.build_candidate_search_string(c) for c in candidates]
    candidate_ids = [c["candidate_id"] for c in candidates]

    t2 = time.time()
    logger.info(f"  Built {len(texts):,} search strings in {t2 - t1:.1f}s")

    # ── Step 3: Encode embeddings in batches ──────────────────────
    logger.info(f"Step 3/4: Encoding embeddings (batch_size={args.batch_size})...")
    logger.info("  Loading sentence-transformers model (first time downloads ~90 MB)...")

    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize=False,  # We normalise inside CandidateFaissIndex.add_vectors()
    )
    embeddings = embeddings.astype(np.float32)

    t3 = time.time()
    throughput = n_candidates / (t3 - t2)
    logger.info(
        f"  Encoded {n_candidates:,} candidates in {t3 - t2:.1f}s "
        f"({throughput:.0f} candidates/sec)"
    )
    logger.info(f"  Embedding matrix shape: {embeddings.shape}, dtype: {embeddings.dtype}")

    # ── Step 4: Build & save FAISS index ─────────────────────────
    logger.info("Step 4/4: Building FAISS index and saving to disk...")

    faiss_index = CandidateFaissIndex(dimension=EMBEDDING_DIM)
    faiss_index.add_vectors(embeddings, candidate_ids)
    faiss_index.save(index_path)

    t4 = time.time()
    index_size_mb = os.path.getsize(index_path) / (1024 * 1024)
    meta_size_kb = os.path.getsize(index_path + ".meta") / 1024

    logger.info("=" * 60)
    logger.info("Index build complete!")
    logger.info(f"  Candidates indexed : {n_candidates:,}")
    logger.info(f"  Total elapsed time : {t4 - t0:.1f}s")
    logger.info(f"  FAISS index size   : {index_size_mb:.1f} MB  →  {index_path}")
    logger.info(f"  Metadata size      : {meta_size_kb:.1f} KB  →  {index_path}.meta")
    logger.info(f"  Embedding dim      : {EMBEDDING_DIM}")
    logger.info(f"  Throughput (encode): {throughput:.0f} cands/sec")
    logger.info("=" * 60)
    logger.info("You can now start the API server. It will auto-load this index.")


if __name__ == "__main__":
    main()
