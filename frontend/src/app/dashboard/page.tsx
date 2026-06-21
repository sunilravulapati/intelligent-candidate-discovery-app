"use client";

import React, { useState, useEffect } from "react";
import SearchPanel from "@/components/SearchPanel";
import AnalyticsCards from "@/components/AnalyticsCards";
import ResultsTable from "@/components/ResultsTable";
import CandidateList from "@/components/CandidateList";
import CandidateDetail from "@/components/CandidateDetail";
import { searchCandidates, checkBackendHealth, CandidateMatch, SearchMetrics, HealthStatus } from "@/lib/api";

export default function Dashboard() {
  const [candidates, setCandidates] = useState<CandidateMatch[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Custom states for ATS workspace
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(null);
  const [isSearchCollapsed, setIsSearchCollapsed] = useState(false);
  const [queryTitle, setQueryTitle] = useState("");
  const [querySkills, setQuerySkills] = useState<string[]>([]);
  
  // Health check states
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Load health check on mount
  useEffect(() => {
    async function fetchHealth() {
      try {
        const status = await checkBackendHealth();
        setHealth(status);
        // Set candidate count immediately from cache info if present
        if (status.system_ready && status.datasets.active_source) {
          const source = status.datasets.active_source;
          const details = (status.datasets as any)[source];
          setMetrics({
            candidates_indexed: source === "challenge_sample" ? 300 : 5000,
            retrieval_pool_size: 0,
            avg_match_score: 0.0,
            retrieval_time_ms: 0,
            ranking_time_ms: 0,
            total_time_ms: 0,
            retrieval_mode: "keyword",
            top_skills_found: []
          });
        }
      } catch (err: any) {
        console.error("Health check failed:", err);
        setError("Could not connect to the backend server. Make sure it is running on port 8000.");
      } finally {
        setHealthLoading(false);
      }
    }
    fetchHealth();
  }, []);

  const handleSearch = async (title: string, description: string, skills: string[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await searchCandidates(title, description, skills);
      setCandidates(response.results);
      setMetrics(response.metrics);
      
      // Save query parameters for the ribbon
      setQueryTitle(title);
      setQuerySkills(skills);
      
      // Auto-select first candidate
      if (response.results.length > 0) {
        setSelectedCandidate(response.results[0]);
      } else {
        setSelectedCandidate(null);
      }
      
      // Collapse search filters after execution
      setIsSearchCollapsed(true);
    } catch (err: any) {
      setError(err.message || "Failed to search candidates.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewCandidate = (candidate: CandidateMatch) => {
    setSelectedCandidate(candidate);
    setIsSearchCollapsed(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Background Orbs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10" />
      <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-3xl -z-10 animate-pulse" />
      
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-950/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">
                Redrob Intelligent Discovery
              </h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                Recruiter Workspace & Analytics
              </p>
            </div>
          </div>

          {/* Connection Status indicator */}
          <div className="flex items-center gap-2">
            {healthLoading ? (
              <span className="text-xs text-slate-500 animate-pulse">Connecting...</span>
            ) : health?.system_ready ? (
              <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full text-xs font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>Active: {health.mode}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 bg-rose-500/10 text-rose-400 border border-rose-500/20 px-3 py-1 rounded-full text-xs font-medium">
                <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                <span>Offline: Check Backend Connection</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 flex flex-col gap-6 overflow-hidden">
        
        {/* Error Callout */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 flex items-start gap-3 text-rose-300 text-sm">
            <svg className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <span className="font-semibold">Query Execution Error:</span> {error}
            </div>
          </div>
        )}

        {/* Sleek Horizontal Ribbon for Collapsed Search */}
        {isSearchCollapsed && (
          <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-5 shadow-2xl relative overflow-hidden group select-none shrink-0 flex items-center justify-between gap-4">
            <div className="absolute -inset-px bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-2xl blur opacity-30 group-hover:opacity-40 transition duration-1000" />
            
            <div className="relative flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-tr from-indigo-500/20 to-purple-600/20 border border-indigo-500/30 rounded-xl flex items-center justify-center text-indigo-400">
                <svg className="w-5 h-5 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-bold text-slate-100 tracking-tight leading-none">
                  {queryTitle}
                </div>
                <div className="flex flex-wrap gap-1.5 text-xs text-slate-450 font-medium">
                  {querySkills.length > 0 ? (
                    querySkills.map((s, idx) => (
                      <span key={idx} className="after:content-['•'] after:mx-1.5 last:after:content-none font-mono">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="italic text-slate-500">No explicit skill keywords required</span>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={() => setIsSearchCollapsed(false)}
              className="relative bg-slate-950 border border-slate-850 hover:border-indigo-500/40 text-slate-300 font-semibold py-2.5 px-4.5 rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-lg hover:shadow-indigo-500/5 duration-300 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Refine Search</span>
            </button>
          </div>
        )}

        {/* Analytics Section */}
        <AnalyticsCards metrics={metrics} />

        {/* Split-Pane layout vs Query Form & Results Table grid */}
        {isSearchCollapsed && candidates.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[600px] lg:h-[calc(100vh-330px)] overflow-hidden">
            {/* Left Column: Scrollable Candidate list */}
            <div className="lg:col-span-5 h-full overflow-hidden">
              <CandidateList
                candidates={candidates}
                selectedCandidate={selectedCandidate}
                onSelectCandidate={setSelectedCandidate}
              />
            </div>
            {/* Right Column: Scrollable Candidate details */}
            <div className="lg:col-span-7 h-full overflow-hidden">
              <CandidateDetail candidate={selectedCandidate} />
            </div>
          </div>
        ) : (
          /* Original Query Form Grid */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
            <div className="lg:col-span-1">
              <SearchPanel onSearch={handleSearch} isLoading={isLoading} />
            </div>
            <div className="lg:col-span-2">
              <ResultsTable 
                candidates={candidates} 
                onViewCandidate={handleViewCandidate}
              />
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/20 py-5 text-center text-xs text-slate-600 mt-auto shrink-0 select-none">
        <p>© 2026 Redrob AI Challenge. All Rights Reserved. Powered by XGBoost, FAISS, and Sentence-Transformers.</p>
      </footer>
    </div>
  );
}
