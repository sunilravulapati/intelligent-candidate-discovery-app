"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";
import CandidateDrawer from "./CandidateDrawer";

interface ResultsTableProps {
  candidates: CandidateMatch[];
}

export default function ResultsTable({ candidates }: ResultsTableProps) {
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const openDrawer = (cand: CandidateMatch) => {
    setSelectedCandidate(cand);
    setIsDrawerOpen(true);
  };

  const getScoreBadgeClass = (score: number) => {
    if (score >= 0.75) return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    if (score >= 0.55) return "bg-indigo-500/10 text-indigo-400 border border-indigo-500/30";
    if (score >= 0.35) return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
  };

  const getSemanticBarColor = (pct: number) => {
    if (pct >= 75) return "bg-gradient-to-r from-violet-500 to-purple-500";
    if (pct >= 50) return "bg-gradient-to-r from-indigo-500 to-violet-500";
    if (pct >= 25) return "bg-gradient-to-r from-sky-500 to-indigo-500";
    return "bg-slate-600";
  };

  // Detect retrieval mode from first result (consistent across all)
  const retrievalMode = candidates.length > 0 ? candidates[0].retrieval_mode : null;

  return (
    <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
      {/* Header row */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          Ranked Candidates
        </h2>
        {/* Retrieval Mode Badge */}
        {retrievalMode && (
          <span className={`text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border flex items-center gap-1.5 ${
            retrievalMode === "semantic"
              ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
              : "bg-amber-500/10 text-amber-400 border-amber-500/20"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${
              retrievalMode === "semantic" ? "bg-violet-400 animate-pulse" : "bg-amber-400"
            }`} />
            {retrievalMode === "semantic" ? "🔷 Semantic Mode" : "⬡ Keyword Fallback"}
          </span>
        )}
      </div>

      {candidates.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
          <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-slate-400 font-medium">No results to display.</p>
          <p className="text-slate-600 text-xs mt-1">Submit a search query on the left to invoke retrieval.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-4 px-3">Candidate</th>
                <th className="py-4 px-3 text-center">Overall</th>
                <th className="py-4 px-3 text-center">Semantic</th>
                <th className="py-4 px-3 text-center">Skills</th>
                <th className="py-4 px-3 text-center">Exp</th>
                <th className="py-4 px-3">Company</th>
                <th className="py-4 px-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-sm">
              {candidates.map((cand) => (
                <tr key={cand.candidate_id} className="hover:bg-slate-800/10 transition duration-150 group">
                  {/* Candidate name + headline */}
                  <td className="py-4 px-3">
                    <div>
                      <div className="font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors">
                        {cand.name}
                      </div>
                      <div className="text-slate-500 text-xs mt-0.5 truncate max-w-[180px]">
                        {cand.headline}
                      </div>
                    </div>
                  </td>

                  {/* Overall Score badge */}
                  <td className="py-4 px-3 text-center">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono ${getScoreBadgeClass(cand.overall_score)}`}>
                      {(cand.overall_score * 100).toFixed(0)}%
                    </span>
                  </td>

                  {/* Semantic Match % */}
                  <td className="py-4 px-3 text-center">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-violet-300 font-medium font-mono text-xs">
                        {cand.semantic_similarity_percent}%
                      </span>
                      <div className="w-14 bg-slate-950 rounded-full h-1 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getSemanticBarColor(cand.semantic_similarity_percent)}`}
                          style={{ width: `${cand.semantic_similarity_percent}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Skill Match % */}
                  <td className="py-4 px-3 text-center">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-indigo-300 font-medium font-mono text-xs">
                        {cand.skills_match_percent}%
                      </span>
                      <div className="w-14 bg-slate-950 rounded-full h-1 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full"
                          style={{ width: `${cand.skills_match_percent}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Experience */}
                  <td className="py-4 px-3 text-center text-slate-300 font-mono text-xs whitespace-nowrap">
                    {cand.years_of_experience}y
                  </td>

                  {/* Company */}
                  <td className="py-4 px-3 text-slate-400 text-xs truncate max-w-[120px]">
                    {cand.current_company}
                  </td>

                  {/* View Match */}
                  <td className="py-4 px-3 text-right">
                    <button
                      onClick={() => openDrawer(cand)}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:underline inline-flex items-center gap-1 transition-all"
                    >
                      <span>View Match</span>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Candidate Details Drawer */}
      <CandidateDrawer
        candidate={selectedCandidate}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
