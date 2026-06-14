import sys
import os
import argparse
import logging

# Ensure backend directory is in python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion.ingestion_service import IngestionService
from app.services.embeddings.embeddings_service import EmbeddingsService
from app.services.retrieval.retrieval_service import RetrievalService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="CLI utility to generate dense embeddings for candidates and save to FAISS vector index."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for generating embeddings (default: 64)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=-1,
        help="Limit the number of candidates embedded for testing (default: all)."
    )
    args = parser.parse_args()

    logger.info("Initializing services...")
    ingestion = IngestionService()
    retrieval = RetrievalService()
    
    logger.info("Loading candidates for indexing...")
    candidates = ingestion.load_all_candidates(limit=args.limit)
    if not candidates:
        logger.error("No candidates found to generate embeddings for.")
        sys.exit(1)
        
    logger.info(f"Loaded {len(candidates)} candidates. Beginning embedding generation...")
    
    # We leverage RetrievalService to build and persist the index dynamically
    retrieval.candidates_cache = {c["candidate_id"]: c for c in candidates}
    retrieval._build_index_dynamically(ingestion)
    
    logger.info("Embeddings generation and FAISS indexing completed successfully.")


if __name__ == "__main__":
    main()
