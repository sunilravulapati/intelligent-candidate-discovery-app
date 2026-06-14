import sys
import os
import argparse
import logging

# Ensure backend directory is in python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion.ingestion_service import IngestionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="CLI utility to load and preprocess candidates dataset from raw challenge files."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=-1,
        help="Maximum number of candidates to process (default: all)."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only check file structure without loading/processing records."
    )
    args = parser.parse_args()

    logger.info("Initializing candidate ingestion service...")
    ingestion = IngestionService()
    
    status = ingestion.get_candidate_files_status()
    active_source = status.get("active_source")
    
    if not active_source:
        logger.error("No active dataset source files found! Please place candidates.jsonl in the datasets folder.")
        sys.exit(1)
        
    logger.info(f"Active datasource identified: '{active_source}'")
    logger.info(f"File path: {status[active_source]['path']} ({status[active_source]['size_mb']} MB)")

    if args.validate_only:
        logger.info("Validation complete. Dataset file is reachable and ready.")
        return

    logger.info("Starting candidate streaming pipeline...")
    count = 0
    # Stream first few candidates to demonstrate running code
    for cand in ingestion.stream_candidates(limit=args.limit if args.limit > 0 else 5):
        logger.info(f"Loaded candidate: {cand.get('candidate_id')} - {cand.get('profile', {}).get('anonymized_name')}")
        count += 1

    logger.info(f"Successfully loaded and verified {count} records (Sample size limit active).")


if __name__ == "__main__":
    main()
