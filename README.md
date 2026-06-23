# TalentLens — AI-Powered Semantic Candidate Discovery

TalentLens is a state-of-the-art AI semantic matching engine that connects recruiters to ideal engineering candidates in seconds. Unlike traditional keyword-based matching, TalentLens understands the implicit contextual requirements of a job description and surfaces top-tier engineering talent from a pool of nearly 100k profiles, re-ranked via a custom XGBoost model.

---

## Features

- **Semantic Candidate Matching** — Leverages dense vector embeddings and FAISS to match candidates conceptually against unstructured job descriptions in milliseconds.
- **Explainable AI Ranking** — A proprietary multi-stage ML pipeline providing explainable scoring breakdowns across Skills, Experience, Role Fit, and Semantic Similarity.
- **Executive Recruiter Summaries** — Automated generation of succinct, executive-style candidate insights detailing precise matches and technical gaps.
- **Real-time Comparative Analytics** — Direct side-by-side Candidate Comparison Engine with automated "Winner" highlighting across core technical capabilities.
- **Premium Workspace & Workflow** — Recruiter-first dashboard with 1-click shortlist tracking, exporting (CSV/JSON), and dynamic interaction history logs.
- **Lightning Fast Evaluation** — Deep pipeline profiling demonstrating semantic query and retrieval times directly to the end user.

---

## Architecture

TalentLens employs a robust, highly optimized retrieval-augmented ranking architecture.

A Next.js (App Router) frontend speaks to a Python FastAPI backend. The backend manages a FAISS vector index of candidate embeddings. Candidate retrieval happens via high-dimensional semantic search, which is then fed into a highly-tuned XGBoost regressor for final feature-based re-ranking based on domain experience, skills matching, and engagement signals.

```
Job Description (unstructured text)
        │
        ▼
  HuggingFace Embeddings
        │
        ▼
  FAISS Vector Search  ──── Top-K candidates retrieved
        │
        ▼
  XGBoost Re-Ranker   ──── Skills / Experience / Role Fit / Semantic Score
        │
        ▼
  FastAPI Response    ──── Next.js Recruiter Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Vanilla CSS / Tailwind utilities |
| Backend | Python, FastAPI |
| Vector Search | FAISS |
| ML Ranking | XGBoost, Pandas |
| Embeddings | HuggingFace / Transformers |

---

## Project Structure

```
├── data/          # Local CSV/JSONL dataset directory 
├── backend/       # FastAPI app — routes, settings, service orchestration, ML models, CLI utils
└── frontend/      # Next.js 15 Tailwind recruiter dashboard
```

---

## Local Development Setup

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server (choose one)
python -m app.run
uvicorn app.main:app --reload     # with hot reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose (run both together)

```bash
docker-compose up --build
```

---

## Deployment

> Add deployed links here.

---

## Demo

> Add Loom video link here.

---

## License

> Add license information here.
