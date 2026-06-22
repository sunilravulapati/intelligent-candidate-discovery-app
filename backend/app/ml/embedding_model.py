import numpy as np
from typing import List, Union
import logging
import time

# Embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384
logger = logging.getLogger(__name__)
_ENCODE_CALLS = 0


class CandidateEmbeddingModel:
    """
    Orchestrates candidate and job text embedding generation using Sentence-Transformers.
    Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast on CPU).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None  # Loaded lazily

    def _load_model(self) -> None:
        """Loads the SentenceTransformer model lazily to save startup memory."""
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.info(f"Loading SentenceTransformer model '{self.model_name}' locally (local_files_only=True)...")
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
                logger.info("Successfully loaded SentenceTransformer model from local cache.")
            except Exception as e:
                logger.warning(
                    f"Failed to load SentenceTransformer model locally ({e}). "
                    "Attempting remote download/validation from Hugging Face Hub..."
                )
                self.model = SentenceTransformer(self.model_name, local_files_only=False)
                logger.info("Successfully loaded SentenceTransformer model remotely.")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 64,
        show_progress_bar: bool = False,
        normalize: bool = False,
    ) -> np.ndarray:
        """
        Generates dense vector embeddings for a given text or list of texts.

        Args:
            texts: Single string or list of strings to embed.
            batch_size: Batch size used during encoding (relevant for large lists).
            show_progress_bar: Show tqdm progress bar during encoding.
            normalize: If True, L2-normalise the output vectors (for cosine similarity).

        Returns:
            np.ndarray: Float32 vector(s) of shape (N, EMBEDDING_DIM) or (EMBEDDING_DIM,).
        """
        self._load_model()
        if self.model is None:
            raise RuntimeError("SentenceTransformer model failed to load.")

        global _ENCODE_CALLS
        _ENCODE_CALLS += 1
        item_count = 1 if isinstance(texts, str) else len(texts)
        t_start = time.time()
        logger.info(
            "EMBED MODEL ENCODE START call=%s items=%s batch_size=%s normalize=%s",
            _ENCODE_CALLS,
            item_count,
            batch_size,
            normalize,
        )
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )
        encode_ms = (time.time() - t_start) * 1000
        logger.info(
            "EMBED MODEL ENCODE END call=%s items=%s duration_ms=%.2f",
            _ENCODE_CALLS,
            item_count,
            encode_ms,
        )
        embeddings = embeddings.astype(np.float32)

        if normalize:
            import faiss
            if len(embeddings.shape) == 1:
                embeddings = embeddings.reshape(1, -1)
                faiss.normalize_L2(embeddings)
                embeddings = embeddings[0]
            else:
                faiss.normalize_L2(embeddings)

        return embeddings

    def build_candidate_search_string(self, candidate_profile: dict) -> str:
        """
        Builds a rich composite text from a candidate profile for semantic indexing.

        Combines:
          - Professional headline
          - Profile summary
          - Skills (with proficiency level)
          - Current role and company
          - Experience titles and abbreviated descriptions (first 120 chars each)

        Args:
            candidate_profile: Deserialized candidate profile schema dictionary.

        Returns:
            str: Combined textual representation of the candidate.
        """
        profile = candidate_profile.get("profile", {})
        headline = profile.get("headline", "")
        summary = profile.get("summary", "")
        current_title = profile.get("current_title", "")
        current_company = profile.get("current_company", "")

        # Skills with proficiency
        skills_list = candidate_profile.get("skills", [])
        skill_parts = []
        for s in skills_list:
            name = s.get("name", "")
            proficiency = s.get("proficiency", "")
            if name:
                skill_parts.append(f"{name} ({proficiency})" if proficiency else name)
        skills_text = ", ".join(skill_parts)

        # Experience: titles + companies
        experience_parts = []
        for exp in candidate_profile.get("career_history", []):
            title = exp.get("title", "")
            company = exp.get("company", "")
            if title:
                experience_parts.append(f"{title} at {company}")
        experience_text = " | ".join(experience_parts)

        parts = [
            f"Headline: {headline}",
            f"Current Role: {current_title} at {current_company}",
            f"Summary: {summary}",
            f"Skills: {skills_text}",
            f"Experience: {experience_text}",
        ]
        return ". ".join(p for p in parts if p.split(": ", 1)[-1].strip())

    def build_job_query_string(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str] | None = None,
    ) -> str:
        """
        Builds a symmetric job query embedding text for retrieval.

        Args:
            job_title: Job title.
            job_description: Full job description.
            required_skills: Optional list of required skills.

        Returns:
            str: Composite query text for embedding.
        """
        skills_text = ", ".join(required_skills) if required_skills else ""
        parts = [
            f"Job Title: {job_title}",
            f"Description: {job_description}",
        ]
        if skills_text:
            parts.append(f"Required Skills: {skills_text}")
        return ". ".join(parts)
