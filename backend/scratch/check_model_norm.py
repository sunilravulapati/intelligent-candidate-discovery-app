import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.ml.embedding_model import CandidateEmbeddingModel

model = CandidateEmbeddingModel()
text = "Backend Engineer specializing in Python."
vec_unnorm = model.encode(text, batch_size=1, normalize=False)
print("Unnormalized norm:", np.linalg.norm(vec_unnorm))
