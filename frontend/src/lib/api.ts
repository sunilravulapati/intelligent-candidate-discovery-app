export interface Skill {
  name: string;
  proficiency: string;
  endorsements: number;
  duration_months: number;
}

export interface Experience {
  company: string;
  title: string;
  start_date: string;
  end_date: string | null;
  duration_months: number;
  is_current: boolean;
  industry: string;
  company_size: string;
  description: string;
}

export interface ExpectedSalaryRange {
  min: number;
  max: number;
}

export interface ActivitySignals {
  profile_completeness_score: number;
  signup_date: string;
  last_active_date: string;
  open_to_work_flag: boolean;
  profile_views_received_30d: number;
  applications_submitted_30d: number;
  recruiter_response_rate: number;
  avg_response_time_hours: number;
  skill_assessment_scores: Record<string, number>;
  connection_count: number;
  endorsements_received: number;
  notice_period_days: number;
  expected_salary_range_inr_lpa: ExpectedSalaryRange;
  preferred_work_mode: string;
  willing_to_relocate: boolean;
  github_activity_score: number;
  search_appearance_30d: number;
  saved_by_recruiters_30d: number;
  interview_completion_rate: number;
  offer_acceptance_rate: number;
  verified_email: boolean;
  verified_phone: boolean;
  linkedin_connected: boolean;
}

export interface CandidateMatch {
  candidate_id: string;
  name: string;
  headline: string;
  current_title: string;
  rank: number;
  /** Legacy: equals overall_score */
  match_score: number;
  /** Role / title alignment × 100 */
  role_fit_percent: number;
  /** Required skill coverage × 100 */
  skill_fit_percent: number;
  /** Semantic similarity × 100 */
  semantic_fit_percent: number;
  semantic_similarity_percent: number;
  title_alignment_percent: number;
  skills_match_percent: number;
  matched_skills: string[];
  missing_skills: string[];
  ranking_reasons: string[];
  experience_score: number;
  activity_score: number;
  overall_score: number;
  years_of_experience: number;
  current_company: string;
  explanation: string;
  retrieval_mode: "semantic" | "keyword";
  skills: Skill[];
  career_history: Experience[];
  redrob_signals: ActivitySignals;
}

export interface SearchMetrics {
  candidates_indexed: number;
  retrieval_pool_size: number;
  avg_match_score: number;
  retrieval_time_ms: number;
  embedding_time_ms?: number;
  faiss_time_ms?: number;
  ranking_time_ms: number;
  explainability_time_ms?: number;
  total_time_ms: number;
  retrieval_mode: string;
  embedding_cache_hit?: boolean;
  embedding_calls_per_request?: number;
  embedding_calls_per_session?: number;
  embedding_cache_hits_per_session?: number;
  embedding_cache_misses_per_session?: number;
  top_skills_found: string[];
  timing_breakdown?: Record<string, number>;
}

export interface JobSearchResponse {
  metrics: SearchMetrics;
  results: CandidateMatch[];
}

/** Browser calls same-origin /api (proxied by Next.js). SSR uses BACKEND_URL directly. */
function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    return "";
  }
  const url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${getApiBaseUrl()}${path}`;
  try {
    return await fetch(url, init);
  } catch (err) {
    const hint =
      typeof window !== "undefined"
        ? " Make sure the FastAPI backend is running (cd backend && python -m app.run)."
        : "";
    const message = err instanceof Error ? err.message : "Network request failed";
    throw new Error(`${message}.${hint}`);
  }
}

export async function searchCandidates(
  title: string,
  description: string,
  requiredSkills: string[] = [],
  top_k: number = 10
): Promise<JobSearchResponse> {
  const response = await apiFetch("/api/jobs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      description,
      required_skills: requiredSkills,
      top_k,
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `Search failed (${response.status}).`);
  }

  return response.json();
}

export async function generateSubmission(
  title: string,
  description: string,
  requiredSkills: string[] = []
): Promise<void> {
  const response = await apiFetch("/api/jobs/submission", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      description,
      required_skills: requiredSkills,
      top_k: 100, // Export more candidates for submission
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `Submission generation failed (${response.status}).`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "submission.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export interface HealthStatus {
  status: string;
  system_ready: boolean;
  database: {
    connected: boolean;
    details: string;
  };
  datasets: {
    active_source: string | null;
    challenge_jsonl: { exists: boolean; size_mb: number };
    challenge_sample: { exists: boolean; size_mb: number };
    local_raw_jsonl: { exists: boolean; size_mb: number };
  };
  mode: string;
  semantic_mode?: {
    active: boolean;
    index_loaded: boolean;
    index_path: string;
    candidates_indexed: number;
  };
  startup_status?: {
    cache_loaded: boolean;
    index_loaded: boolean;
    model_loaded: boolean;
    ranking_loaded: boolean;
    ready: boolean;
    startup_time_ms: number;
    timing_breakdown?: Record<string, number>;
  };
}

export async function checkBackendHealth(): Promise<HealthStatus> {
  const response = await apiFetch("/api/health", {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}. Is the API server running on port 8000?`);
  }

  return response.json();
}
