import numpy as np
from typing import List, Union
import logging
import time
import threading

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
        self._load_lock = threading.Lock()
        self._load_count = 0

    def _load_model(self) -> None:
        """Loads the SentenceTransformer model lazily to save startup memory."""
        if self.model is not None:
            return
        with self._load_lock:
            if self.model is not None:
                return
            from sentence_transformers import SentenceTransformer
            import torch
            import logging
            logger = logging.getLogger(__name__)
            t0 = time.perf_counter()
            try:
                # NOTE: Do NOT call torch.set_num_threads(1) here.
                # Setting threads=1 forces all transformer matrix multiplications onto a
                # single CPU core, which is the root cause of 2-5 second encode times.
                # PyTorch defaults to using all available cores — leave it that way.
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
            self._load_count += 1
            logger.info(
                "MODEL ID: %s | load_count=%s | load_time_ms=%.2f | torch_threads=%s",
                id(self.model),
                self._load_count,
                (time.perf_counter() - t0) * 1000,
                torch.get_num_threads(),
            )

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

        import torch
        global _ENCODE_CALLS
        _ENCODE_CALLS += 1
        item_count = 1 if isinstance(texts, str) else len(texts)
        t_start = time.perf_counter()
        logger.info(
            "EMBED START call=%s MODEL ID=%s load_count=%s items=%s normalize=%s torch_threads=%s",
            _ENCODE_CALLS,
            id(self.model),
            self._load_count,
            item_count,
            normalize,
            torch.get_num_threads(),
        )

        with torch.no_grad():
            t0 = time.perf_counter()
            all_embeddings = []
            
            if isinstance(texts, str):
                texts = [texts]
                
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                # 1. Preprocessing
                features = self.model.tokenize(batch_texts)
                features = {
                    k: v.to(self.model.device) if isinstance(v, torch.Tensor) else v
                    for k, v in features.items()
                }

                # 2. Model Encode
                out_features = self.model(features)

                # 3. Postprocessing
                embeddings = out_features["sentence_embedding"]
                if isinstance(embeddings, torch.Tensor):
                    embeddings = embeddings.cpu().numpy()
                embeddings = embeddings.astype(np.float32)

                if normalize:
                    import faiss
                    if len(embeddings.shape) == 1:
                        embeddings = embeddings.reshape(1, -1)
                        faiss.normalize_L2(embeddings)
                    else:
                        faiss.normalize_L2(embeddings)
                
                all_embeddings.append(embeddings)
                
            final_embeddings = np.vstack(all_embeddings) if len(all_embeddings) > 1 else all_embeddings[0]
            if item_count == 1 and final_embeddings.shape[0] == 1:
                final_embeddings = final_embeddings[0]

        encode_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            "EMBED END call=%s items=%s total_ms=%.2f",
            _ENCODE_CALLS,
            item_count,
            encode_ms,
        )

        return final_embeddings

        # Log detailed timing breakdown in the console
        print("\n================ EMBEDDING DETAILED TIMINGS ================")
        print(f"Preprocessing: {t_preprocess:.2f}ms")
        print(f"Model Encode: {t_model_encode:.2f}ms")
        print(f"Postprocessing: {t_postprocess:.2f}ms")
        print(f"Total Model Encode Step: {encode_ms:.2f}ms")
        print("============================================================\n")

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

        Generates a *synthetic candidate profile* that mirrors the structure
        produced by ``build_candidate_search_string()``.  This is critical
        because all-MiniLM-L6-v2 is a symmetric bi-encoder — if the query
        and document text structures diverge, cosine similarity collapses.

        Strategy:
          1. Headline = job_title
          2. Current Role = job_title
          3. Summary = concise professional summary derived from the JD
             (NOT the raw JD — that would be too long and structurally wrong).
          4. Skills = comma-separated required_skills
          5. Experience = job_title (mimics career_history entries)

        The summary is capped to ~120 words to stay within the model's
        256-token window.
        """
        skills_text = ", ".join(required_skills) if required_skills else ""

        # Build a concise professional summary from the JD instead of
        # dumping the entire description.  Extract the first few sentences
        # and rewrite in candidate-profile style.
        summary = self._extract_concise_summary(job_title, job_description, skills_text)

        parts = [
            f"Headline: {job_title}",
            f"Current Role: {job_title}",
            f"Summary: {summary}",
            f"Skills: {skills_text}",
            f"Experience: {job_title}",
        ]
        return ". ".join(parts)

    @staticmethod
    def _extract_concise_summary(
        job_title: str,
        description: str,
        skills_text: str,
        max_words: int = 120,
    ) -> str:
        """
        Produces a candidate-style summary paragraph from a job description.

        Instead of dumping the raw JD (which is structurally different from a
        candidate summary), this synthesises a first-person-style professional
        summary:

            "Professional {title} experienced in {skills}.
             {key requirements extracted from JD}."

        This stays concise enough for the 256-token model window and
        structurally aligned with how candidate profiles are embedded.
        """
        import re

        # Start with a synthetic opening that mirrors candidate profiles
        opening = f"Professional {job_title.lower()} experienced in {skills_text}" if skills_text else f"Experienced {job_title.lower()}"

        # Extract meaningful sentences from the JD (skip very short fragments)
        sentences = re.split(r'[.!?\n]+', description)
        meaningful = []
        word_count = len(opening.split())

        for sent in sentences:
            sent = sent.strip()
            # Skip very short fragments, headers, and bullet-point noise
            if len(sent.split()) < 4:
                continue
            # Skip sentences that are just skill lists (already in Skills field)
            if sent.lower().startswith(("required", "requirements", "qualifications", "nice to have", "what you")):
                continue
            word_count += len(sent.split())
            if word_count > max_words:
                break
            meaningful.append(sent)

        if meaningful:
            return f"{opening}. {'. '.join(meaningful)}"
        return opening

