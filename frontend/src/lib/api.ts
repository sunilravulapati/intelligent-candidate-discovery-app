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
  /** Legacy: equals overall_score */
  match_score: number;
  /** Cosine similarity from FAISS × 100, 0 in keyword mode */
  semantic_similarity_percent: number;
  /** Jaccard skill overlap × 100 */
  skills_match_percent: number;
  /** Final hybrid weighted score (0-1) */
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
  ranking_time_ms: number;
  total_time_ms: number;
  retrieval_mode: string;
  top_skills_found: string[];
}

export interface JobSearchResponse {
  metrics: SearchMetrics;
  results: CandidateMatch[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function searchCandidates(
  title: string,
  description: string,
  requiredSkills: string[] = []
): Promise<JobSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      description,
      required_skills: requiredSkills,
      top_k: 10,
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || "Failed to search candidates.");
  }

  return response.json();
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
}

export async function checkBackendHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Backend service is currently unreachable.");
  }

  return response.json();
}
