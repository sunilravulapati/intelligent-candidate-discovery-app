# ── Root-level Dockerfile ────────────────────────────────────────────────────
# Build context is the ENTIRE repository root.
# This ensures data/ (FAISS index + candidates) is available alongside the app.
#
# Render config: set "Dockerfile Path" to ./Dockerfile (this file)
# and "Docker Build Context Directory" to . (repo root)
#
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./

# Copy data directory (FAISS index + candidate datasets) into the image
# This makes data/ available at /app/../data == /data relative to WORKDIR,
# but we place it at /data explicitly and override the env vars.
COPY data/ /data/

EXPOSE 8000

# DATA_DIR and FAISS_INDEX_PATH are set to absolute container paths
# so they resolve correctly regardless of working directory.
ENV DATA_DIR=/data
ENV FAISS_INDEX_PATH=/data/embeddings/faiss_candidates.index

CMD ["python", "app/run.py"]
