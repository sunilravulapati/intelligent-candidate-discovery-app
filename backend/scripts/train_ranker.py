import sys
import os
import argparse
import logging
import numpy as np
import pandas as pd

# Ensure backend directory is in python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.feature_engineering import XGBoostFeatureEngineer
from app.ml.ranker import CandidateRanker
from app.services.ingestion.ingestion_service import IngestionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="CLI utility to train the XGBoost candidate ranking model."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)."
    )
    args = parser.parse_args()

    logger.info("Initializing ML components...")
    ingestion = IngestionService()
    feature_engineer = XGBoostFeatureEngineer()
    ranker = CandidateRanker()

    logger.info("Loading candidates for training...")
    candidates = ingestion.load_all_candidates(limit=200)
    if not candidates:
        logger.error("No training data available.")
        sys.exit(1)

    logger.info("Building training features...")
    # Mock a training job query
    job_query = {
        "title": "Senior Backend Developer",
        "description": "Looking for a seasoned developer with Python, PostgreSQL, and AWS skills.",
        "required_skills": ["Python", "Postgres", "Aws"]
    }
    
    feature_df = feature_engineer.batch_extract_features(job_query, candidates)
    
    # Generate mock relevance labels (targets) and query groups for demonstration
    targets = np.random.randint(0, 3, size=len(feature_df))  # Labels: 0 (non-match) to 2 (great-match)
    groups = np.array([len(feature_df)])  # Single query group containing all candidates
    
    logger.info(f"Feature matrix shape: {feature_df.shape}. Targets size: {len(targets)}.")
    logger.info(f"Training XGBoost Ranker for {args.epochs} iterations...")
    
    # Run training (automatically saves to default path inside data/processed/)
    ranker.train(feature_df, targets, groups)
    
    logger.info("Ranker model training completed and saved to disk.")


if __name__ == "__main__":
    main()
