"use client";

import React from "react";
import { CandidateMatch } from "@/lib/api";

interface CandidateListProps {
  candidates: CandidateMatch[];
  selectedCandidate: CandidateMatch | null;
  onSelectCandidate: (candidate: CandidateMatch) => void;
}

export default function CandidateList({
  candidates,
  selectedCandidate,
  onSelectCandidate,
}: CandidateListProps) {
  const getScoreColorClass = (score: number) => {
    if (score >= 0.75) return "text-emerald-400 font-bold";
    if (score >= 0.55) return "text-indigo-400 font-bold";
    if (score >= 0.35) return "text-amber-400 font-bold";
    return "text-slate-400 font-bold";
  };

  const getSemanticColorClass = (pct: number) => {
    if (pct >= 75) return "text-violet-400 font-medium";
    if (pct >= 50) return "text-indigo-400 font-medium";
    return "text-slate-400 font-medium";
  };

  const getSkillsColorClass = (pct: number) => {
    if (pct >= 75) return "text-purple-400 font-medium";
    if (pct >= 50) return "text-indigo-400 font-medium";
    return "text-slate-400 font-medium";
  };

  // Detect retrieval mode from first result (consistent across all)
  const retrievalMode = candidates.length > 0 ? candidates[0].retrieval_mode : null;

  return (
    <div className="flex flex-col h-full bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header bar */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span className="text-sm font-bold text-slate-200">
            Candidates ({candidates.length})
          </span>
        </div>
        {retrievalMode && (
          <span className={`text-[9px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full border flex items-center gap-1 ${
            retrievalMode === "semantic"
              ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
              : "bg-amber-500/10 text-amber-400 border-amber-500/20"
          }`}>
            {retrievalMode === "semantic" ? "Semantic" : "Keyword"}
          </span>
        )}
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5 custom-scrollbar">
        {candidates.map((cand) => {
          const isSelected = selectedCandidate?.candidate_id === cand.candidate_id;
          return (
            <button
              key={cand.candidate_id}
              onClick={() => onSelectCandidate(cand)}
              className={`w-full text-left p-3.5 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col gap-2 relative overflow-hidden group select-none ${
                isSelected
                  ? "bg-indigo-950/20 border-indigo-500/80 shadow-md shadow-indigo-500/5"
                  : "bg-slate-900/30 border-slate-800/80 hover:bg-slate-800/30 hover:border-slate-700/60"
              }`}
            >
              {/* Highlight bar */}
              {isSelected && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 to-purple-600 rounded-r" />
              )}

              {/* Title & Name info */}
              <div className="flex justify-between items-start gap-2">
                <div className="truncate">
                  <div className={`font-bold text-sm transition-colors group-hover:text-indigo-300 ${
                    isSelected ? "text-indigo-200" : "text-slate-200"
                  }`}>
                    {cand.name}
                  </div>
                  <div className="text-[11px] text-slate-400 font-medium truncate mt-0.5">
                    {cand.headline}
                  </div>
                </div>
              </div>

              {/* Scores row */}
              <div className="flex items-center gap-1.5 text-[11px] bg-slate-950/40 border border-slate-800/50 rounded-lg p-1.5 select-none font-mono">
                <div className="flex-1 text-center border-r border-slate-800/50">
                  <span className="text-slate-500 font-sans mr-0.5 text-[9px] uppercase tracking-wider">Overall:</span>
                  <span className={getScoreColorClass(cand.overall_score)}>
                    {(cand.overall_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex-1 text-center border-r border-slate-800/50">
                  <span className="text-slate-500 font-sans mr-0.5 text-[9px] uppercase tracking-wider">Sem:</span>
                  <span className={getSemanticColorClass(cand.semantic_similarity_percent)}>
                    {cand.semantic_similarity_percent}%
                  </span>
                </div>
                <div className="flex-1 text-center">
                  <span className="text-slate-500 font-sans mr-0.5 text-[9px] uppercase tracking-wider">Skills:</span>
                  <span className={getSkillsColorClass(cand.skills_match_percent)}>
                    {cand.skills_match_percent}%
                  </span>
                </div>
              </div>

              {/* Company & experience metadata */}
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium select-none">
                <span className="truncate pr-2">
                  {cand.current_company || "No Company"}
                </span>
                <span className="shrink-0 bg-slate-900/60 border border-slate-800/60 text-slate-400 px-1.5 py-0.5 rounded text-[10px] font-mono">
                  {cand.years_of_experience} yrs
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
