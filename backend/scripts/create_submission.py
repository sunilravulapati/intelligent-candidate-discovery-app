import sys
import os
import argparse
import logging
import pandas as pd

# Ensure backend directory is in python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion.ingestion_service import IngestionService
from app.services.embeddings.embeddings_service import EmbeddingsService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import RankingService
from app.services.explainability.explainability_service import ExplainabilityService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="CLI utility to generate final challenge submission CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../data/submissions/submission.csv",
        help="Path where the final ranked CSV will be written (default: ../data/submissions/submission.csv)."
    )
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info("Initializing services...")
    ingestion = IngestionService()
    embeddings = EmbeddingsService()
    retrieval = RetrievalService()
    ranking = RankingService()
    explainability = ExplainabilityService()

    # Mock Job Query (For the final challenge, this should read from the challenge job description file)
    job_title = "Data Scientist / AI Engineer"
    job_desc = "Seeking an AI expert with strong Python, XGBoost, and sentence-transformers experience."
    req_skills = ["Python", "XGBoost", "Sentence-Transformers"]

    logger.info(f"Using query: Job Title: '{job_title}'")
    
    # 1. Embed job query
    job_emb = embeddings.generate_job_embedding(job_title, job_desc)

    # 2. Retrieve candidates
    logger.info("Retrieving candidates via FAISS...")
    retrieved = retrieval.retrieve_candidates(job_emb, ingestion, top_k=100)
    if not retrieved:
        logger.error("No candidates retrieved. Submission file cannot be created.")
        sys.exit(1)

    candidates_list = [c for c, _ in retrieved]

    # 3. Re-rank candidates
    logger.info("Re-ranking candidates via XGBoost...")
    ranked = ranking.rank_retrieved_candidates(job_title, job_desc, req_skills, candidates_list)

    # 4. Generate final CSV dataframe
    submission_rows = []
    for rank_idx, cand in enumerate(ranked):
        cand_id = cand.get("candidate_id")
        score = cand.get("match_score", 0.0)
        
        # Scale score to a normalized range for submission formatting if necessary
        scaled_score = min(max(score, 0.0), 1.0)
        
        # Generate short explanation summary
        reasoning = explainability.generate_explanation(job_title, req_skills, cand)
        
        submission_rows.append({
            "candidate_id": cand_id,
            "rank": rank_idx + 1,
            "score": f"{scaled_score:.4f}",
            "reasoning": reasoning
        })

    df = pd.DataFrame(submission_rows)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Submission CSV file successfully created at {output_path}")
    logger.info(f"Total rows written: {len(df)}")


if __name__ == "__main__":
    main()
