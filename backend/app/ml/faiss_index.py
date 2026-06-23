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
            # Inner Product (Cosine similarity when normalized) but with HNSW graph for fast approximate search
            self.index = faiss.IndexHNSWFlat(self.dimension, 32, faiss.METRIC_INNER_PRODUCT)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 64

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

        The query_vector MUST already be L2-normalised before calling this method
        (retrieval_service.py passes encode(..., normalize=True) which handles this).
        Do NOT re-normalize inside this method — that is redundant and wastes CPU.

        Args:
            query_vector: Dense search vector, already L2-normalised.
            top_k: Number of nearest matches to return.

        Returns:
            List[Tuple[str, float]]: List of (candidate_id, similarity_score).
        """
        import logging
        import time
        _log = logging.getLogger(__name__)

        # Memory/Disk Check placeholders inside FAISS search
        # We don't read_index or JSON load here, but we will log if we did.
        import time

        self._init_index()
        if self.index is None or self.index.ntotal == 0:
            return []

        import faiss
        
        t0 = time.perf_counter()
        
        # 1. Query reshaping / dimension check
        if len(query_vector.shape) == 1:
            query_vector = np.expand_dims(query_vector, axis=0)
        t_reshape = time.perf_counter()
        reshape_ms = (t_reshape - t0) * 1000

        # 3. index.search()
        distances, indices = self.index.search(query_vector, top_k)
        t_search = time.perf_counter()
        raw_search_ms = (t_search - t_reshape) * 1000
        
        print(f"[RAW FAISS SEARCH] {raw_search_ms:.2f}ms type={type(self.index).__name__} ntotal={self.index.ntotal}")

        # 4. ID extraction / lookup
        raw_hits = list(zip(distances[0], indices[0]))
        t_extract = time.perf_counter()
        id_extraction_ms = (t_extract - t_search) * 1000

        # 6. Metadata lookup & filtering (Result building)
        results = []
        for dist, idx in raw_hits:
            if idx != -1 and idx < len(self.candidate_ids):
                results.append((self.candidate_ids[idx], float(dist)))
        t_metadata = time.perf_counter()
        metadata_lookup_ms = (t_metadata - t_extract) * 1000

        # POST_PROCESSING
        t_post = time.perf_counter()
        post_process_ms = (t_post - t_metadata) * 1000

        total_ms = (time.perf_counter() - t0) * 1000

        print("\n==================================================")
        print("FAISS SEARCH INTERNAL BREAKDOWN")
        print("===============================")
        print(f"NORMALIZE           : 0.00 ms (done externally)")
        print(f"RESHAPE             : {reshape_ms:.2f} ms")
        print(f"RAW_SEARCH          : {raw_search_ms:.2f} ms")
        print(f"ID_EXTRACTION       : {id_extraction_ms:.2f} ms")
        print(f"LOOKUP              : {metadata_lookup_ms:.2f} ms")
        print(f"RESULT_BUILD        : 0.00 ms")
        print(f"POST_PROCESS        : {post_process_ms:.2f} ms")
        print(f"TOTAL               : {total_ms:.2f} ms")
        print("==========================\n")

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
