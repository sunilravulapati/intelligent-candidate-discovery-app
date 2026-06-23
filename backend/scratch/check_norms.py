import numpy as np
import os

path = r"C:\work\redrob_ai\intelligent-candidate-discovery\data\embeddings\faiss_candidates.index.checkpoint.npz"
with np.load(path, allow_pickle=True) as data:
    vectors = data["embeddings"]

norms = np.linalg.norm(vectors, axis=1)
print(f"Loaded {len(vectors)} vectors.")
print(f"Norms - min: {np.min(norms):.4f}, max: {np.max(norms):.4f}, mean: {np.mean(norms):.4f}")
