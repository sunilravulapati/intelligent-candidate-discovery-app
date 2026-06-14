# Phase 2 Gap Analysis: Semantic Candidate Retrieval

Generated: 2026-06-14

---

## Summary Table

| Component | File | Status | Gap |
|---|---|---|---|
| Embedding Model | `ml/embedding_model.py` | ⚠️ Partial | Missing rich text builder, job query builder, batch_size param |
| FAISS Index | `ml/faiss_index.py` | ⚠️ Partial | Missing `is_loaded()` method |
| Index Build Script | `scripts/build_semantic_index.py` | ❌ Missing | Does not exist (only `generate_embeddings.py` with broken call) |
| Retrieval Service | `services/retrieval/retrieval_service.py` | ❌ Missing | No semantic search, no FAISS load, no `is_semantic_ready()` |
| Hybrid Ranking | `services/ranking/ranking_service.py` | ❌ Missing | No hybrid scorer, only XGBoost skeleton |
| Explainability | `services/explainability/explainability_service.py` | ⚠️ Partial | No semantic score in reason text |
| Jobs API | `api/v1/endpoints/jobs.py` | ❌ Missing | Jaccard-only; no semantic pipeline, no new response fields |
| Frontend Types | `frontend/src/lib/api.ts` | ❌ Missing | No `semantic_similarity_percent`, `overall_score`, `retrieval_mode` |
| Results Table | `frontend/src/components/ResultsTable.tsx` | ❌ Missing | No Semantic Match column, no Overall Score column |
| Dashboard | `frontend/src/app/dashboard/page.tsx` | ❌ Missing | No retrieval mode badge |
| Candidate Drawer | `frontend/src/components/CandidateDrawer.tsx` | ⚠️ Partial | Only 2 score gauges; no semantic gauge |

---

## 1. Embedding Layer (`ml/embedding_model.py`) — ⚠️ Partial

### What exists
- `CandidateEmbeddingModel` class with lazy model load via `sentence-transformers`
- `encode()` wrapping `model.encode()` with `convert_to_numpy=True`
- `build_candidate_search_string()` using headline + summary + skills list

### What is missing
- **Rich text**: experience titles/descriptions and current role are excluded from the composite text
- **Job query builder**: No `build_job_query_string()` for symmetric job-side embedding
- **Batch size control**: `encode()` doesn't expose `batch_size` or `show_progress_bar`
- **Dimension constant**: Hard-coded as 384 in `faiss_index.py`, not exported from model

### Recommended changes
- Enrich `build_candidate_search_string()` with experience job titles and role descriptions
- Add `build_job_query_string(title, description, required_skills)` 
- Add `batch_size` and `show_progress_bar` params to `encode()`

---

## 2. FAISS Index (`ml/faiss_index.py`) — ⚠️ Partial

### What exists
- `CandidateFaissIndex` using `IndexFlatIP` (correct for cosine after L2-norm)
- L2 normalization on both add and search vectors
- `save()` / `load()` with `.meta` pickle sidecar for `candidate_ids`
- Valid `search()` returning `(candidate_id, score)` tuples

### What is missing
- **`is_loaded()`**: No way for retrieval service to check if index is ready without inspecting internals
- **`ntotal` property**: No public accessor for index size

### Recommended changes
- Add `def is_loaded(self) -> bool: return self.index is not None and self.index.ntotal > 0`

---

## 3. Index Build Script (`scripts/generate_embeddings.py`) — ❌ Broken / Wrong

### What exists
- `generate_embeddings.py` calls `retrieval._build_index_dynamically(ingestion)` — **this method does not exist** on `RetrievalService`, causing an `AttributeError` at runtime
- No performance timing or progress bar

### What is missing
- A complete, working `build_semantic_index.py` that: streams candidates → builds embeddings in batches → saves FAISS index

### Recommended changes
- Create `scripts/build_semantic_index.py` as a clean standalone script
- Keep broken `generate_embeddings.py` as-is (do not delete, just supersede)

---

## 4. Retrieval Service (`services/retrieval/retrieval_service.py`) — ❌ Missing

### What exists
- `RetrievalService` loads all candidates into `candidates_cache` dict on first call
- `retrieve_candidates()` just returns the first `top_k` items with a dummy score of `0.5`
- `load_index_and_cache()` correctly populates the dict from ingestion

### What is missing
- **FAISS integration**: No loading of `faiss_candidates.index`, no semantic search
- **`is_semantic_ready()`**: No public method to check semantic availability
- **Fallback logic**: No graceful degradation to keyword mode when index absent
- **Embedding at query time**: No `EmbeddingsService` usage in the retrieval path

### Recommended changes
- At startup: try loading FAISS index → set `_semantic_ready` flag
- `retrieve_candidates()`: if semantic ready → embed job query → FAISS search → lookup profiles; else return all cached candidates (fallback for Jaccard in jobs.py)
- Expose `is_semantic_ready() -> bool`

---

## 5. Ranking Service (`services/ranking/ranking_service.py`) — ❌ Missing

### What exists
- `RankingService` delegates to `XGBoostFeatureEngineer` + `CandidateRanker`
- `CandidateRanker.predict_scores()` falls back to a skill+exp+github heuristic if no model file found
- Feature engineer produces `skill_overlap_ratio`, `years_of_experience`, `github_activity_score`

### What is missing
- **Hybrid ranking**: No `hybrid_rank()` method with weighted combination
- **Semantic similarity component**: Not included in any existing score path
- **Activity score composite**: Not normalized or weighted per spec
- **Experience match normalization**: Not capped/normalized to [0,1]
- **Configurable weights**: Hardcoded in `predict_scores()` fallback, not exposed

### Recommended changes
- Add `hybrid_rank(job_title, required_skills, candidates_with_semantic_scores, weights=None)` to `RankingService`
- Weight formula: `0.50 * semantic + 0.20 * skill_overlap + 0.15 * experience_match + 0.15 * activity_score`
- activity_score = `0.4 * open_to_work + 0.3 * completeness/100 + 0.2 * response_rate + 0.1 * clamp(github,0,100)/100`
- experience_match = `min(years, 15) / 15`

---

## 6. Explainability Service (`services/explainability/explainability_service.py`) — ⚠️ Partial

### What exists
- `generate_explanation()` returning structured "Matched / Missing / Reason" text
- Reason includes experience years, skill overlap %, open-to-work, github score

### What is missing
- **Semantic score**: Not included in reason text
- **Hybrid breakdown**: No mention of the 4-component score

### Recommended changes
- Add optional `semantic_similarity: float` param to `generate_explanation()`
- Include in reason: "Strong semantic alignment with {job_title} requirements ({pct}% semantic match)"

---

## 7. Jobs API (`api/v1/endpoints/jobs.py`) — ❌ Missing semantic pipeline

### What exists
- Full Jaccard-based pipeline: skill overlap + title similarity → sort → explainability
- Returns `match_score`, `skills_match_percent`, `explanation`, plus nested `skills`, `career_history`, `redrob_signals`

### What is missing
- **Semantic retrieval call**: No `RetrievalService.retrieve_candidates()` usage for FAISS
- **Hybrid ranking call**: Uses manual inline Jaccard, not `RankingService.hybrid_rank()`
- **Response fields**: No `semantic_similarity_percent`, `overall_score`, `retrieval_mode`
- **Top-500 intermediate step**: Goes directly to top_k without pre-filtering

### Recommended changes
- Replace inline scoring with: semantic retrieval → hybrid ranking → top_k slice
- Add 3 new response fields to `CandidateMatchResponse` and populate them
- Pass `retrieval_service.is_semantic_ready()` to choose `retrieval_mode`

---

## 8. Frontend Types (`frontend/src/lib/api.ts`) — ❌ Missing

### What exists
- `CandidateMatch` with `match_score`, `skills_match_percent`, full nested types

### What is missing
- `semantic_similarity_percent: number`
- `overall_score: number`
- `retrieval_mode: "semantic" | "keyword"`

---

## 9. Results Table (`frontend/src/components/ResultsTable.tsx`) — ❌ Missing

### What exists
- Score badge column (shows `match_score`)
- Skills Match % column with progress bar

### What is missing
- **Semantic Match %** column with indigo progress bar
- **Overall Score** replacing or supplementing the current score badge
- The current "Score" column shows raw Jaccard `match_score`, not the hybrid `overall_score`

---

## 10. Dashboard (`frontend/src/app/dashboard/page.tsx`) — ❌ Missing

### What exists
- Health status badge (semantic/keyword mode absent)
- Analytics cards showing `candidates_indexed`, `avg_match_score`, `retrieval_time_ms`

### What is missing
- **Retrieval mode badge**: `🔷 Semantic Mode` or `⬡ Keyword Fallback` based on last result's `retrieval_mode`

---

## 11. Candidate Drawer (`frontend/src/components/CandidateDrawer.tsx`) — ⚠️ Partial

### What exists
- 2-column score grid: Match Score + Skills Match
- Full skill overlap breakdown (matched/missing pills)
- Experience timeline, Skills grid, Activity Signals grid

### What is missing
- **3rd score gauge**: Semantic Match % with its own card
- Adjusting the layout from 2-col to 3-col for scores

---

## Performance Bottlenecks

| Bottleneck | Root Cause | Impact | Fix |
|---|---|---|---|
| Cold start: ~3-5s first request | `candidates_cache` loads 100K records from JSONL on first POST | High latency for first recruiter | Move to app startup via lifespan event |
| No FAISS: O(N) full scan | Jaccard computed over all 100K candidates inline | ~2-5s per query at scale | FAISS top-500 pre-filter → rank only 500 |
| Embedding per-query: N/A now | Embeddings not used at runtime yet | Blocked on FAISS integration | Offline index build; query embeds only once |
| `RankingService` init on every request | `XGBoostFeatureEngineer` and `CandidateRanker` instantiated in `Depends()` | Overhead per request | Use singleton via `app.state` |

---

## Implementation Priority

1. **`ml/embedding_model.py`** — add rich text builder + job query builder (30 min)
2. **`ml/faiss_index.py`** — add `is_loaded()` (5 min)
3. **`scripts/build_semantic_index.py`** — new working build script (30 min)
4. **`services/retrieval/retrieval_service.py`** — semantic retrieval + fallback + `is_semantic_ready()` (45 min)
5. **`services/ranking/ranking_service.py`** — `hybrid_rank()` (30 min)
6. **`services/explainability/explainability_service.py`** — add semantic score to reason (15 min)
7. **`api/v1/endpoints/jobs.py`** — new pipeline + new response fields (45 min)
8. **`frontend/src/lib/api.ts`** — add 3 new fields (5 min)
9. **`frontend/src/components/ResultsTable.tsx`** — Semantic Match column (15 min)
10. **`frontend/src/app/dashboard/page.tsx`** — retrieval mode badge (10 min)
11. **`frontend/src/components/CandidateDrawer.tsx`** — 3rd score gauge (15 min)
