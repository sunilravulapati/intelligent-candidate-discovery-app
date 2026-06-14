import os
from typing import List, Tuple
import numpy as np


class CandidateFaissIndex:
    """
    Wrapper around the FAISS index vector database.
    Manages vector storage, loading/saving indexes, and executing similarity search.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None  # Loaded lazily or built on the fly
        self.candidate_ids: List[str] = []

    def is_loaded(self) -> bool:
        """Returns True if the index is initialised and contains at least one vector."""
        return self.index is not None and self.index.ntotal > 0

    @property
    def ntotal(self) -> int:
        """Number of vectors stored in the index."""
        return self.index.ntotal if self.index is not None else 0

    def _init_index(self) -> None:
        """Initializes empty FAISS index."""
        if self.index is None:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (Cosine similarity when normalized)

    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Adds candidate embeddings with their corresponding IDs to the index.
        
        Args:
            vectors: np.ndarray matrix of candidate embeddings.
            ids: List of candidate IDs corresponding to each vector.
        """
        self._init_index()
        if self.index is None:
            raise RuntimeError("FAISS index could not be initialized.")

        # L2 normalization for cosine similarity
        import faiss
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.candidate_ids.extend(ids)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Searches candidate index for vectors closest to the query vector.
        
        Args:
            query_vector: Dense search vector (e.g. from job description).
            top_k: Number of nearest matches to return.
            
        Returns:
            List[Tuple[str, float]]: List of (candidate_id, similarity_score).
        """
        self._init_index()
        if self.index is None or self.index.ntotal == 0:
            # Return empty if index is empty
            return []

        import faiss
        # Ensure query_vector has shape (1, dimension)
        if len(query_vector.shape) == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        # L2 normalization for query vector
        query_normalized = query_vector.copy()
        faiss.normalize_L2(query_normalized)

        distances, indices = self.index.search(query_normalized, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.candidate_ids):
                results.append((self.candidate_ids[idx], float(dist)))
        
        return results

    def save(self, file_path: str) -> None:
        """
        Persists the index and list of candidate IDs to file.
        """
        if self.index is None:
            raise ValueError("No active index to save.")
        import faiss
        import pickle
        
        # Save FAISS index
        faiss.write_index(self.index, file_path)
        
        # Save candidate_ids metadata
        meta_path = file_path + ".meta"
        with open(meta_path, "wb") as f:
            pickle.dump(self.candidate_ids, f)

    def load(self, file_path: str) -> None:
        """
        Loads the index and candidate IDs metadata from file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"FAISS index file not found at {file_path}")
        
        import faiss
        import pickle
        
        self.index = faiss.read_index(file_path)
        
        meta_path = file_path + ".meta"
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                self.candidate_ids = pickle.load(f)
        else:
            raise FileNotFoundError(f"FAISS index metadata file not found at {meta_path}")
