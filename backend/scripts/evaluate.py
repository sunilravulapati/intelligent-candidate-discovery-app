import sys
import os
import argparse
import logging
import numpy as np

# Ensure backend directory is in python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.evaluator import ModelEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="CLI utility to evaluate ranker performance using NDCG, MAP, and MRR."
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Evaluate NDCG at K (default: 10)."
    )
    args = parser.parse_args()

    logger.info("Running ranking evaluation pipeline...")

    # Mock recommendations relevance lists for evaluation demonstration
    # List of lists, where each list is the relevance labels of candidate recommendations for a search query
    mock_recommendations = [
        [2, 1, 2, 0, 0, 1, 0, 0, 0, 0],
        [1, 2, 0, 0, 2, 0, 0, 0, 0, 1],
        [2, 2, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 1, 0, 0, 0, 0],
    ]

    mrr = ModelEvaluator.mean_reciprocal_rank(mock_recommendations)
    map_score = ModelEvaluator.mean_average_precision(mock_recommendations)
    ndcg = ModelEvaluator.mean_ndcg_at_k(mock_recommendations, k=args.k)

    print("\n" + "="*40)
    print("Ranking Model Evaluation Metrics")
    print("="*40)
    print(f"Mean Reciprocal Rank (MRR):  {mrr:.4f}")
    print(f"Mean Average Precision (MAP): {map_score:.4f}")
    print(f"NDCG@{args.k}:                     {ndcg:.4f}")
    print("="*40 + "\n")


if __name__ == "__main__":
    main()
