"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";
import { getMatchTier, getMatchTierColor } from "@/lib/ranking";

interface CandidateComparisonProps {
  candidates: CandidateMatch[];
  onClose: () => void;
}

export default function CandidateComparison({ candidates, onClose }: CandidateComparisonProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleCandidate = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      if (next.size < 2) {
        next.add(id);
      }
    }
    setSelectedIds(next);
  };

  const selectedCandidates = candidates.filter((c) => selectedIds.has(c.candidate_id));

  const isWinner = (cand: CandidateMatch, metric: keyof CandidateMatch) => {
    if (selectedCandidates.length !== 2) return false;
    const otherCand = selectedCandidates.find((c) => c.candidate_id !== cand.candidate_id);
    if (!otherCand) return false;
    return (cand[metric] as number) > (otherCand[metric] as number);
  };

  const formatPercent = (value: number | undefined | null) => {
    if (value == null || Number.isNaN(value)) return "0%";
    const pct = value <= 1 && value > 0 ? value * 100 : value;
    return `${Math.round(pct)}%`;
  };

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-6">
      <div className="bg-slate-900 border border-white/[0.08] rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
          <div>
            <h2 className="text-lg font-bold text-white">Compare Candidates</h2>
            <p className="text-xs text-slate-400 mt-1">Select exactly 2 candidates to compare side-by-side.</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-700/50 p-2 rounded-lg transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">
          {/* Sidebar: Candidate Selector */}
          <div className="w-full lg:w-80 border-r border-white/[0.06] bg-slate-950/30 overflow-y-auto p-4 flex flex-col gap-2">
            {candidates.map((cand) => (
              <label
                key={cand.candidate_id}
                className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                  selectedIds.has(cand.candidate_id)
                    ? "bg-violet-500/10 border-violet-500/30"
                    : "bg-slate-900/50 border-white/[0.04] hover:bg-slate-800/50"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(cand.candidate_id)}
                  onChange={() => toggleCandidate(cand.candidate_id)}
                  disabled={!selectedIds.has(cand.candidate_id) && selectedIds.size >= 2}
                  className="mt-1 shrink-0 accent-violet-500 rounded border-white/[0.1] bg-slate-900"
                />
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-white truncate">{cand.name}</div>
                  <div className="text-xs text-slate-400 truncate mt-0.5">{cand.current_title || cand.headline}</div>
                  <div className={`text-[10px] uppercase tracking-wider font-bold mt-1.5 inline-block px-1.5 py-0.5 rounded border ${getMatchTierColor(cand.overall_score)}`}>
                    {getMatchTier(cand.overall_score)}
                  </div>
                </div>
              </label>
            ))}
          </div>

          {/* Main Area: Comparison Table */}
          <div className="flex-1 overflow-y-auto p-6 bg-slate-900 custom-scrollbar">
            {selectedCandidates.length === 2 ? (
              <div className="grid grid-cols-2 gap-6 h-full">
                {selectedCandidates.map((cand) => {
                  const matchedCount = cand.matched_skills?.length || 0;
                  const missingCount = cand.missing_skills?.length || 0;
                  const totalRequiredSkills = matchedCount + missingCount;

                  return (
                  <div key={cand.candidate_id} className="flex flex-col gap-6">
                    <div className="pb-4 border-b border-white/[0.06]">
                      <h3 className="text-xl font-bold text-white truncate">{cand.name}</h3>
                      <p className="text-sm text-violet-300/80 mt-1 truncate">{cand.current_title || cand.headline}</p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">{cand.current_company}</p>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Overall Match</div>
                          {isWinner(cand, "overall_score") && <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">🏆 Better</span>}
                        </div>
                        <div className={`text-sm font-bold uppercase tracking-wider px-2 py-1 rounded border inline-block ${getMatchTierColor(cand.overall_score)}`}>
                          {getMatchTier(cand.overall_score)} ({formatPercent(cand.overall_score)})
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Skill Match</div>
                          {isWinner(cand, "skill_fit_percent") && <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">🏆 Better</span>}
                        </div>
                        <div className="text-sm font-medium text-slate-200">
                          {formatPercent(cand.skill_fit_percent)}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1">
                          {matchedCount} of {totalRequiredSkills} required skills matched
                        </div>
                        <div className="flex gap-4 mt-2">
                          <div>
                            <div className="text-[9px] uppercase tracking-wider text-emerald-500/80 font-bold mb-1">Matched Skills ({matchedCount})</div>
                            <div className="flex flex-wrap gap-1">
                              {cand.matched_skills?.map((s) => <span key={s} className="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[10px]">{s}</span>)}
                              {matchedCount === 0 && <span className="text-[10px] text-slate-500">None</span>}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-4 mt-2">
                          <div>
                            <div className="text-[9px] uppercase tracking-wider text-rose-500/80 font-bold mb-1">Missing Skills ({missingCount})</div>
                            <div className="flex flex-wrap gap-1">
                              {cand.missing_skills?.map((s) => <span key={s} className="px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px]">{s}</span>)}
                              {missingCount === 0 && <span className="text-[10px] text-slate-500">None</span>}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Semantic Match</div>
                          {isWinner(cand, "semantic_fit_percent") && <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">🏆 Better</span>}
                        </div>
                        <div className="text-sm font-medium text-slate-200">
                          {formatPercent(cand.semantic_fit_percent)} contextual alignment
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Experience</div>
                          {isWinner(cand, "years_of_experience") && <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">🏆 Better</span>}
                        </div>
                        <div className="text-sm font-medium text-slate-200">
                          {cand.years_of_experience} years
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Role Alignment</div>
                          {isWinner(cand, "role_fit_percent") && <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">🏆 Better</span>}
                        </div>
                        <div className="text-sm font-medium text-slate-200">
                          {formatPercent(cand.role_fit_percent)} fit
                        </div>
                      </div>
                    </div>
                  </div>
                )})}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
                <div className="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center mb-4 border border-white/[0.04]">
                  <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-slate-400">Select two candidates from the sidebar<br/>to compare their profiles.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
