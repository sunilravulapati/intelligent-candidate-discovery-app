"use client";

import React, { useState, useEffect, useRef } from "react";
import SearchPanel from "@/components/SearchPanel";
import SearchSummaryHeader from "@/components/SearchSummaryHeader";
import SearchLoadingOverlay from "@/components/SearchLoadingOverlay";
import AnalyticsCards from "@/components/AnalyticsCards";
import CandidateList from "@/components/CandidateList";
import CandidateDetail from "@/components/CandidateDetail";
import CandidateComparison from "@/components/CandidateComparison";
import { searchCandidates, checkBackendHealth, CandidateMatch, SearchMetrics, HealthStatus } from "@/lib/api";
import * as XLSX from "xlsx";
import Papa from "papaparse";

const DEFAULT_TITLE = "Backend Engineer";
const DEFAULT_DESCRIPTION =
  "We are looking for a backend engineer experienced in building scalable web APIs. The candidate should be proficient in Python, FastAPI, and PostgreSQL. Experience with FAISS, search algorithms, and vector embeddings is a strong plus.";
const DEFAULT_SKILLS = "Python, FastAPI, PostgreSQL, FAISS";
const SEARCH_STATE_KEY = "redrob.discovery.dashboard.v1";

interface PersistedDashboardState {
  // Only search form fields are persisted — never results, metrics, or rankings.
  queryTitle: string;
  queryDescription: string;
  querySkillsText: string;
}

export interface SearchHistoryItem {
  id: string;
  queryTitle: string;
  queryDescription: string;
  querySkillsText: string;
  timestamp: number;
}

const SEARCH_HISTORY_KEY = "redrob.discovery.searchHistory.v1";

function loadSearchHistory(): SearchHistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(SEARCH_HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function loadPersistedFormFields(): PersistedDashboardState | null {
  if (typeof window === "undefined") return null;

  try {
    const rawState = window.localStorage.getItem(SEARCH_STATE_KEY);
    if (!rawState) return null;

    const saved = JSON.parse(rawState) as Partial<PersistedDashboardState>;
    return {
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
  const [restoredState] = useState<PersistedDashboardState | null>(() => loadPersistedFormFields());
  // Never restore old results, metrics, rankings, or selected candidates.
  // Only the search form fields are preserved across sessions.
  const [candidates, setCandidates] = useState<CandidateMatch[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(null);
  const [isSearchCollapsed, setIsSearchCollapsed] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [showCompare, setShowCompare] = useState(false);

  const [queryTitle, setQueryTitle] = useState(() => restoredState?.queryTitle ?? DEFAULT_TITLE);
  const [queryDescription, setQueryDescription] = useState(() => restoredState?.queryDescription ?? DEFAULT_DESCRIPTION);
  const [querySkillsText, setQuerySkillsText] = useState(() => restoredState?.querySkillsText ?? DEFAULT_SKILLS);

  const searchGenerationRef = useRef(0);
  const searchStartTimeRef = useRef<number | null>(null);
  const hasRestoredStateRef = useRef(true);

  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>(() => loadSearchHistory());

  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const querySkills = querySkillsText
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);

  useEffect(() => {
    if (!hasRestoredStateRef.current) return;

    const stateToPersist: PersistedDashboardState = {
      queryTitle,
      queryDescription,
      querySkillsText,
    };

    window.localStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(stateToPersist));
  }, [
    queryDescription,
    querySkillsText,
    queryTitle,
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
        setError("Workspace is initializing. Please wait a moment and try again.");
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

    // Update search history
    const newItem: SearchHistoryItem = {
      id: Math.random().toString(36).substr(2, 9),
      queryTitle: title,
      queryDescription: description,
      querySkillsText: skills.join(", "),
      timestamp: Date.now(),
    };
    setSearchHistory((prev) => {
      const deduped = prev.filter(h => h.queryTitle.toLowerCase() !== title.toLowerCase() || h.querySkillsText !== skills.join(", "));
      const next = [newItem, ...deduped].slice(0, 5);
      if (typeof window !== "undefined") window.localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(next));
      return next;
    });

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
    } catch {
      if (generation !== searchGenerationRef.current) return;
      setError("Unable to retrieve candidates. Please retry your search.");
    } finally {
      if (generation === searchGenerationRef.current) {
        setIsLoading(false);
      }
    }
  };

  const handleRefineSearch = () => {
    setIsSearchCollapsed(false);
  };

  const applyHistoryItem = (item: SearchHistoryItem) => {
    setQueryTitle(item.queryTitle);
    setQueryDescription(item.queryDescription);
    setQuerySkillsText(item.querySkillsText);
  };

  const prepareExportData = async () => {
    setIsLoading(true);
    try {
      const skills = querySkillsText.split(",").map(s => s.trim()).filter(Boolean);
      const response = await searchCandidates(queryTitle, queryDescription, skills, 100);
      return response.results.map(c => ({
        "candidate_id": c.candidate_id,
        "rank": c.rank,
        "score": c.overall_score.toFixed(4),
        "reasoning": c.ranking_reasons.join(". ") + "."
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = async () => {
    const data = await prepareExportData();
    const csv = Papa.unparse(data);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "ranked_candidates.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportExcel = async () => {
    const data = await prepareExportData();
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Candidates");
    XLSX.writeFile(workbook, "ranked_candidates.xlsx");
  };

  const isWorkspaceReady = health?.startup_status?.ready ?? false;

  if (!isWorkspaceReady) {
    const startupStatus = health?.startup_status as Record<string, unknown> | undefined;
    const cache_loaded = (startupStatus?.cache_loaded as boolean) ?? false;
    const index_loaded = (startupStatus?.index_loaded as boolean) ?? false;
    const model_loaded = (startupStatus?.model_loaded as boolean) ?? false;
    const ranking_loaded = (startupStatus?.ranking_loaded as boolean) ?? false;
    const startup_time_ms = (startupStatus?.startup_time_ms as number) ?? 0;
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
            <h2 className="text-lg font-semibold text-white mb-2">Preparing Semantic Workspace</h2>
            <p className="text-slate-500 text-sm mb-6">Loading candidate index and semantic retrieval engine…</p>

            <div className="space-y-2 text-left text-sm">
              {[
                { label: "Candidate Cache", done: cache_loaded },
                { label: "FAISS Vector Index", done: index_loaded },
                { label: "Embedding Model", done: model_loaded },
                { label: "Ranking Engine", done: ranking_loaded },
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
            {startup_time_ms > 0 && (
              <p className="text-[10px] text-slate-600 mt-1 uppercase tracking-wider">Startup: {(startup_time_ms / 1000).toFixed(1)}s</p>
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
              <h1 className="text-base font-semibold text-white tracking-tight">TalentLens</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">AI-Powered Candidate Intelligence</p>
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
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 flex items-center justify-between shadow-lg shadow-rose-500/5">
            <span className="text-sm font-medium text-rose-300">{error}</span>
            <button
              onClick={() => {
                setError(null);
                if (health?.startup_status?.ready) {
                  const skills = querySkillsText.split(",").map(s => s.trim()).filter(Boolean);
                  if (queryTitle && queryDescription) {
                    handleSearch(queryTitle, queryDescription, skills);
                  }
                }
              }}
              className="text-xs font-bold uppercase tracking-wider text-rose-400 hover:text-rose-200 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg cursor-pointer transition-colors"
            >
              Retry
            </button>
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
            onCompare={() => setShowCompare(true)}
            onExportCSV={handleExportCSV}
            onExportExcel={handleExportExcel}
          />
        )}

        <AnalyticsCards
          metrics={metrics}
          hasSearched={hasSearched && candidates.length > 0}
          bestScore={candidates[0]?.overall_score}
          queryTitle={queryTitle}
          queryDescription={queryDescription}
          querySkills={querySkills}
        />

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
            <div className="lg:col-span-8 h-full flex items-center justify-center">
              <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl w-full max-w-2xl p-10 shadow-2xl backdrop-blur-xl relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.05] to-purple-500/[0.05] pointer-events-none" />
                <div className="relative flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-6 text-indigo-400">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-3 tracking-tight">Find the Best Candidate</h2>
                  <p className="text-slate-400 max-w-md mx-auto leading-relaxed text-sm mb-4">
                    AI-powered semantic ranking across nearly 100k candidate profiles.<br/>
                    Enter a role description to begin.
                  </p>
                  
                  <div className="mt-8 w-full text-left grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <h3 className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-3 border-b border-white/[0.06] pb-2">Example Searches</h3>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { title: "Frontend Lead", desc: "React expert with 5+ years building scalable UI architectures.", skills: "React, TypeScript, Redux" },
                          { title: "Machine Learning Engineer", desc: "NLP and computer vision specialist with production model deployment.", skills: "Python, PyTorch, AWS" }
                        ].map((ex, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              setQueryTitle(ex.title);
                              setQueryDescription(ex.desc);
                              setQuerySkillsText(ex.skills);
                            }}
                            className="bg-slate-900/60 border border-white/[0.08] hover:border-indigo-500/50 hover:bg-indigo-500/10 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer text-left w-full"
                          >
                            <div className="font-semibold">{ex.title}</div>
                            <div className="text-[10px] text-slate-500 mt-0.5 truncate">{ex.skills}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {searchHistory.length > 0 && (
                      <div>
                        <h3 className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-3 border-b border-white/[0.06] pb-2">Recent Searches</h3>
                        <div className="flex flex-col gap-2">
                          {searchHistory.map(h => (
                            <button
                              key={h.id}
                              onClick={() => applyHistoryItem(h)}
                              className="bg-slate-900/60 border border-white/[0.08] hover:border-indigo-500/50 hover:bg-indigo-500/10 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer text-left w-full"
                            >
                              <div className="font-semibold">{h.queryTitle}</div>
                              <div className="text-[10px] text-slate-500 mt-0.5 truncate">{h.querySkillsText}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {showCompare && (
        <CandidateComparison candidates={candidates} onClose={() => setShowCompare(false)} />
      )}

      <footer className="border-t border-white/[0.04] py-4 text-center text-[11px] text-slate-600">
        TalentLens · AI-Powered Candidate Intelligence
      </footer>
    </div>
  );
}
