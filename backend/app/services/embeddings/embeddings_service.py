import os
import logging
from typing import List, Dict, Any
import numpy as np
from app.ml.embedding_model import CandidateEmbeddingModel
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Orchestrates the generation of dense vector embeddings for jobs and candidates.
    """

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model = CandidateEmbeddingModel(model_name=model_name)

    def generate_candidate_embeddings(self, candidates: List[Dict[str, Any]]) -> np.ndarray:
        """
        Builds search strings and runs batch embedding generation for a list of candidate profiles.
        
        Args:
            candidates: List of candidate profile schema dictionaries.
            
        Returns:
            np.ndarray: Matrix of embeddings.
        """
        if not candidates:
            return np.empty((0, 384), dtype=np.float32)

        search_strings = [self.model.build_candidate_search_string(c) for c in candidates]
        logger.info(f"Generating embeddings for {len(candidates)} candidates...")
        embeddings = self.model.encode(search_strings)
        return embeddings

    def generate_job_embedding(self, job_title: str, job_description: str) -> np.ndarray:
        """
        Generates embedding for a recruiter query.
        
        Args:
            job_title: Job title.
            job_description: Job description text.
        """
        combined_text = f"Title: {job_title}. Description: {job_description}."
        logger.info(f"Generating embedding for job: '{job_title}'")
        return self.model.encode(combined_text)
