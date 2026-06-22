"use client";

import React, { useState, useEffect, useRef } from "react";
import SearchPanel from "@/components/SearchPanel";
import SearchSummaryHeader from "@/components/SearchSummaryHeader";
import SearchLoadingOverlay from "@/components/SearchLoadingOverlay";
import AnalyticsCards from "@/components/AnalyticsCards";
import ResultsTable from "@/components/ResultsTable";
import CandidateList from "@/components/CandidateList";
import CandidateDetail from "@/components/CandidateDetail";
import { searchCandidates, checkBackendHealth, CandidateMatch, SearchMetrics, HealthStatus } from "@/lib/api";

const DEFAULT_TITLE = "Backend Engineer";
const DEFAULT_DESCRIPTION =
  "We are looking for a backend engineer experienced in building scalable web APIs. The candidate should be proficient in Python, FastAPI, and PostgreSQL. Experience with FAISS, search algorithms, and vector embeddings is a strong plus.";
const DEFAULT_SKILLS = "Python, FastAPI, PostgreSQL, FAISS";
const SEARCH_STATE_KEY = "redrob.discovery.dashboard.v1";

interface PersistedDashboardState {
  candidates: CandidateMatch[];
  metrics: SearchMetrics | null;
  selectedCandidateId: string | null;
  hasSearched: boolean;
  isSearchCollapsed: boolean;
  queryTitle: string;
  queryDescription: string;
  querySkillsText: string;
}

function loadPersistedDashboardState(): PersistedDashboardState | null {
  if (typeof window === "undefined") return null;

  try {
    const rawState = window.localStorage.getItem(SEARCH_STATE_KEY);
    if (!rawState) return null;

    const saved = JSON.parse(rawState) as Partial<PersistedDashboardState>;
    return {
      candidates: Array.isArray(saved.candidates) ? saved.candidates : [],
      metrics: saved.metrics ?? null,
      selectedCandidateId: saved.selectedCandidateId ?? null,
      hasSearched: Boolean(saved.hasSearched),
      isSearchCollapsed: Boolean(saved.isSearchCollapsed),
      queryTitle: saved.queryTitle || DEFAULT_TITLE,
      queryDescription: saved.queryDescription || DEFAULT_DESCRIPTION,
      querySkillsText: saved.querySkillsText || DEFAULT_SKILLS,
    };
  } catch {
    window.localStorage.removeItem(SEARCH_STATE_KEY);
    return null;
  }
}

export default function Dashboard() {
  const [restoredState] = useState<PersistedDashboardState | null>(() => loadPersistedDashboardState());
  const [candidates, setCandidates] = useState<CandidateMatch[]>(() => restoredState?.candidates ?? []);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(() => restoredState?.metrics ?? null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(() => {
    const saved = restoredState;
    if (!saved?.candidates?.length) return null;
    return (
      saved.candidates.find((candidate) => candidate.candidate_id === saved.selectedCandidateId) ??
      saved.candidates[0]
    );
  });
  const [isSearchCollapsed, setIsSearchCollapsed] = useState(() => restoredState?.isSearchCollapsed ?? false);
  const [hasSearched, setHasSearched] = useState(() => restoredState?.hasSearched ?? false);

  const [queryTitle, setQueryTitle] = useState(() => restoredState?.queryTitle ?? DEFAULT_TITLE);
  const [queryDescription, setQueryDescription] = useState(() => restoredState?.queryDescription ?? DEFAULT_DESCRIPTION);
  const [querySkillsText, setQuerySkillsText] = useState(() => restoredState?.querySkillsText ?? DEFAULT_SKILLS);

  const searchGenerationRef = useRef(0);
  const searchStartTimeRef = useRef<number | null>(null);
  const hasRestoredStateRef = useRef(true);

  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const querySkills = querySkillsText
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);

  useEffect(() => {
    if (!hasRestoredStateRef.current) return;

    const stateToPersist: PersistedDashboardState = {
      candidates,
      metrics,
      selectedCandidateId: selectedCandidate?.candidate_id ?? null,
      hasSearched,
      isSearchCollapsed,
      queryTitle,
      queryDescription,
      querySkillsText,
    };

    window.localStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(stateToPersist));
  }, [
    candidates,
    hasSearched,
    isSearchCollapsed,
    metrics,
    queryDescription,
    querySkillsText,
    queryTitle,
    selectedCandidate,
  ]);

  useEffect(() => {
    let timerId: NodeJS.Timeout;

    async function fetchHealth() {
      try {
        const status = await checkBackendHealth();
        setHealth(status);

        const isReady = status.startup_status?.ready ?? status.system_ready;
        if (isReady) {
          setError(null);
          if (status.datasets.active_source) {
            const source = status.datasets.active_source;
            const count = source === "challenge_sample" ? 300 : 99727;
            setMetrics((prev) =>
              prev ?? {
                candidates_indexed: count,
                retrieval_pool_size: 0,
                avg_match_score: 0.0,
                retrieval_time_ms: 0,
                embedding_time_ms: 0,
                faiss_time_ms: 0,
                ranking_time_ms: 0,
                explainability_time_ms: 0,
                total_time_ms: 0,
                retrieval_mode: status.mode.includes("Semantic") ? "semantic" : "keyword",
                top_skills_found: [],
              }
            );
          }
        } else {
          timerId = setTimeout(fetchHealth, 1000);
        }
      } catch {
        setError("Connecting to backend services…");
        timerId = setTimeout(fetchHealth, 1500);
      } finally {
        setHealthLoading(false);
      }
    }
    fetchHealth();

    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, []);

  useEffect(() => {
    if (searchStartTimeRef.current !== null && metrics) {
      const duration = performance.now() - searchStartTimeRef.current;
      const renderMs = Math.round(duration * 100) / 100;
      
      const breakdown = metrics.timing_breakdown || {};
      const embedMs = breakdown["Query Embedding"] || 0;
      const faissMs = breakdown["FAISS Retrieval"] || 0;
      const rankMs = breakdown["Candidate Ranking"] || 0;
      const explainMs = breakdown["Explainability Generation"] || 0;

      console.log("\n================ TIMING BREAKDOWN ================");
      console.log(`Query Embedding: ${embedMs.toFixed(2)}ms`);
      console.log(`FAISS Retrieval: ${faissMs.toFixed(2)}ms`);
      console.log(`Candidate Ranking: ${rankMs.toFixed(2)}ms`);
      console.log(`Explainability Generation: ${explainMs.toFixed(2)}ms`);
      console.log(`Frontend Render: ${renderMs.toFixed(2)}ms`);
      console.log("==================================================\n");

      searchStartTimeRef.current = null;
    }
  }, [candidates, metrics]);

  const handleSearch = async (title: string, description: string, skills: string[]) => {
    const generation = ++searchGenerationRef.current;
    setIsLoading(true);
    setError(null);

    setQueryTitle(title);
    setQueryDescription(description);
    setQuerySkillsText(skills.join(", "));

    try {
      const response = await searchCandidates(title, description, skills);

      if (generation !== searchGenerationRef.current) return;

      // Start measuring render time immediately before updating candidate/metrics state
      searchStartTimeRef.current = performance.now();
      setCandidates(response.results);
      setMetrics(response.metrics);
      setHasSearched(true);

      if (response.results.length > 0) {
        setSelectedCandidate((current) => {
          if (!current) return response.results[0];
          return (
            response.results.find((candidate) => candidate.candidate_id === current.candidate_id) ??
            response.results[0]
          );
        });
      } else {
        setSelectedCandidate(null);
      }

      setIsSearchCollapsed(true);
    } catch (err: unknown) {
      if (generation !== searchGenerationRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to search candidates.");
    } finally {
      if (generation === searchGenerationRef.current) {
        setIsLoading(false);
      }
    }
  };

  const handleRefineSearch = () => {
    setIsSearchCollapsed(false);
  };

  const handleViewCandidate = (candidate: CandidateMatch) => {
    setSelectedCandidate(candidate);
    setIsSearchCollapsed(true);
  };

  const isWorkspaceReady = health?.startup_status?.ready ?? false;

  if (!isWorkspaceReady) {
    const cache_loaded = health?.startup_status?.cache_loaded ?? false;
    const faiss_loaded = health?.startup_status?.faiss_loaded ?? false;
    const model_loaded = health?.startup_status?.model_loaded ?? false;
    const candidatesCount = health?.datasets?.active_source === "challenge_sample" ? "300" : "99,727";

    return (
      <div className="min-h-screen bg-[#0c0d12] text-slate-100 flex flex-col items-center justify-center">
        <div className="max-w-md w-full px-6 py-8 bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] rounded-2xl shadow-2xl">
          <div className="text-center">
            <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-5">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">Preparing Workspace</h2>
            <p className="text-slate-500 text-sm mb-6">Loading candidate index and semantic retrieval engine…</p>

            <div className="space-y-2 text-left text-sm">
              {[
                { label: "Candidate cache", done: cache_loaded },
                { label: "FAISS vector index", done: faiss_loaded },
                { label: "Ranking engine", done: model_loaded },
              ].map((step) => (
                <div key={step.label} className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-white/[0.04]">
                  <span className="text-slate-400">{step.label}</span>
                  <span className={step.done ? "text-emerald-400 text-xs font-medium" : "text-slate-600 text-xs"}>
                    {step.done ? "Ready" : "Loading…"}
                  </span>
                </div>
              ))}
            </div>

            {error && <p className="text-rose-400 text-xs mt-4">{error}</p>}
            {health && (
              <p className="text-[10px] text-slate-600 mt-4 uppercase tracking-wider">{candidatesCount} candidates indexed</p>
            )}
            {healthLoading && !health && (
              <p className="text-[10px] text-slate-600 mt-3">Checking service health...</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  const showWorkspace = isSearchCollapsed && hasSearched && !isLoading;
  const showEmptyResults = hasSearched && !isLoading && candidates.length === 0 && isSearchCollapsed;

  return (
    <div className="min-h-screen bg-[#0c0d12] text-slate-100 flex flex-col">
      <SearchLoadingOverlay isLoading={isLoading} />

      <header className="border-b border-white/[0.06] bg-[#0c0d12]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold text-white tracking-tight">Redrob Discovery</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Recruiter Workspace</p>
            </div>
          </div>

          {health?.system_ready && health?.startup_status?.ready && (
            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {health.mode}
            </div>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-6 flex flex-col gap-5">
        {error && (
          <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        )}

        {isSearchCollapsed && hasSearched && (
          <SearchSummaryHeader
            queryTitle={queryTitle}
            queryDescription={queryDescription}
            querySkills={querySkills}
            metrics={metrics}
            resultCount={candidates.length}
            onRefine={handleRefineSearch}
          />
        )}

        <AnalyticsCards metrics={metrics} hasSearched={hasSearched && candidates.length > 0} />

        {showEmptyResults ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01]">
            <p className="text-lg font-medium text-slate-300">No matching candidates found.</p>
            <p className="text-sm text-slate-500 mt-2 max-w-sm">Try broadening the required skills or adjusting the role title.</p>
            <button
              onClick={handleRefineSearch}
              className="mt-6 px-4 py-2 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer"
            >
              Refine Search
            </button>
          </div>
        ) : showWorkspace && candidates.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[560px] lg:min-h-[calc(100vh-280px)]">
            <div className="lg:col-span-5 h-[480px] lg:h-full">
              <CandidateList
                candidates={candidates}
                selectedCandidate={selectedCandidate}
                onSelectCandidate={setSelectedCandidate}
              />
            </div>
            <div className="lg:col-span-7 h-[560px] lg:h-full">
              <CandidateDetail candidate={selectedCandidate} queryTitle={queryTitle} />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-4">
              <SearchPanel
                onSearch={handleSearch}
                isLoading={isLoading}
                disabled={!isWorkspaceReady}
                title={queryTitle}
                description={queryDescription}
                skillsText={querySkillsText}
                onTitleChange={setQueryTitle}
                onDescriptionChange={setQueryDescription}
                onSkillsTextChange={setQuerySkillsText}
              />
            </div>
            <div className="lg:col-span-8">
              <ResultsTable candidates={isLoading ? [] : candidates} onViewCandidate={handleViewCandidate} isLoading={isLoading} />
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-white/[0.04] py-4 text-center text-[11px] text-slate-600">
        Redrob Intelligent Discovery · Hybrid Semantic Ranking
      </footer>
    </div>
  );
}
