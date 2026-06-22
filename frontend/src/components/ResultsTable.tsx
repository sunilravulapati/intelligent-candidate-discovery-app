"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";
import CandidateDrawer from "./CandidateDrawer";
import { RANKING_FORMULA, rankBadgeClass, scorePercent } from "@/lib/ranking";

interface ResultsTableProps {
  candidates: CandidateMatch[];
  onViewCandidate?: (candidate: CandidateMatch) => void;
  isLoading?: boolean;
}

export default function ResultsTable({ candidates, onViewCandidate, isLoading = false }: ResultsTableProps) {
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const openDrawer = (cand: CandidateMatch) => {
    if (onViewCandidate) {
      onViewCandidate(cand);
    } else {
      setSelectedCandidate(cand);
      setIsDrawerOpen(true);
    }
  };

  const getScoreBadgeClass = (score: number) => {
    const percent = scorePercent(score);
    if (percent >= 75) return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    if (percent >= 55) return "bg-indigo-500/10 text-indigo-400 border border-indigo-500/30";
    if (percent >= 35) return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
  };

  // Detect retrieval mode from first result (consistent across all)
  const retrievalMode = candidates.length > 0 ? candidates[0].retrieval_mode : null;

  return (
    <div className="bg-white/[0.025] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 shadow-[0_18px_70px_rgba(0,0,0,0.28)] relative overflow-hidden">
      {/* Header row */}
      <div className="flex flex-col gap-3 mb-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Ranked Candidates
          </h2>
          <p className="text-xs text-slate-500 mt-1" title="Displayed formula mirrors the current backend hybrid ranker.">
            {RANKING_FORMULA}
          </p>
        </div>
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
            {retrievalMode === "semantic" ? "Semantic Mode" : "Keyword Fallback"}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-16">
          <div className="flex justify-center gap-1.5 mb-4">
            {[0, 1, 2].map((i) => (
              <span key={i} className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" style={{ animationDelay: `${i * 200}ms` }} />
            ))}
          </div>
          <p className="text-slate-400 text-sm">Building your shortlist…</p>
        </div>
      ) : candidates.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-white/[0.06] rounded-xl">
          <p className="text-slate-400 font-medium">No results yet</p>
          <p className="text-slate-600 text-sm mt-1">Run a search to see ranked candidates.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-4 px-3">Rank</th>
                <th className="py-4 px-3">Candidate</th>
                <th className="py-4 px-3 text-center">Overall</th>
                <th className="py-4 px-3 text-center">Role</th>
                <th className="py-4 px-3 text-center">Skills</th>
                <th className="py-4 px-3 text-center">Semantic</th>
                <th className="py-4 px-3 text-center">Exp</th>
                <th className="py-4 px-3">Company</th>
                <th className="py-4 px-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-sm">
              {candidates.map((cand) => (
                <tr key={cand.candidate_id} className="hover:bg-slate-800/10 transition duration-150 group">
                  <td className="py-4 px-3">
                    <span className={`inline-flex h-8 min-w-8 items-center justify-center rounded-lg px-2 text-[10px] font-black ${rankBadgeClass(cand.rank)}`}>
                      #{cand.rank}
                    </span>
                  </td>
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
                      {scorePercent(cand.overall_score)}%
                    </span>
                  </td>

                  {/* Role Fit */}
                  <td className="py-4 px-3 text-center">
                    <span className="text-emerald-300 font-medium font-mono text-xs">
                      {cand.role_fit_percent}%
                    </span>
                  </td>

                  {/* Skill Match */}
                  <td className="py-4 px-3 text-center">
                    <span className="text-indigo-300 font-medium font-mono text-xs">
                      {cand.skill_fit_percent}%
                    </span>
                  </td>

                  {/* Semantic */}
                  <td className="py-4 px-3 text-center">
                    <span className="text-violet-300 font-medium font-mono text-xs">
                      {cand.semantic_fit_percent}%
                    </span>
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
