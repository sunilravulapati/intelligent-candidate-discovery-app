"use client";

import React, { useState, useEffect } from "react";
import SearchPanel from "@/components/SearchPanel";
import AnalyticsCards from "@/components/AnalyticsCards";
import ResultsTable from "@/components/ResultsTable";
import { searchCandidates, checkBackendHealth, CandidateMatch, SearchMetrics, HealthStatus } from "@/lib/api";

export default function Dashboard() {
  const [candidates, setCandidates] = useState<CandidateMatch[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
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
    } catch (err: any) {
      setError(err.message || "Failed to search candidates.");
    } finally {
      setIsLoading(false);
    }
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
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        
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

        {/* Analytics Section */}
        <AnalyticsCards metrics={metrics} />

        {/* Search & Results Panel Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="lg:col-span-1">
            <SearchPanel onSearch={handleSearch} isLoading={isLoading} />
          </div>
          <div className="lg:col-span-2">
            <ResultsTable candidates={candidates} />
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/20 py-6 text-center text-xs text-slate-600 mt-auto">
        <p>© 2026 Redrob AI Challenge. All Rights Reserved. Powered by XGBoost, FAISS, and Sentence-Transformers.</p>
      </footer>
    </div>
  );
}
