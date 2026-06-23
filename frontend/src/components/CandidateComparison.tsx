"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";
import { scorePercent, getMatchTier, getMatchTierColor } from "@/lib/ranking";

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
            className="text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-700/50 p-2 rounded-lg transition-colors"
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
                    ? "bg-indigo-500/10 border-indigo-500/30"
                    : "bg-slate-900/50 border-white/[0.04] hover:bg-slate-800/50"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(cand.candidate_id)}
                  onChange={() => toggleCandidate(cand.candidate_id)}
                  disabled={!selectedIds.has(cand.candidate_id) && selectedIds.size >= 2}
                  className="mt-1 shrink-0 accent-indigo-500 rounded border-white/[0.1] bg-slate-900"
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
          <div className="flex-1 overflow-y-auto p-6 bg-slate-900">
            {selectedCandidates.length === 2 ? (
              <div className="grid grid-cols-2 gap-6 h-full">
                {selectedCandidates.map((cand) => (
                  <div key={cand.candidate_id} className="flex flex-col gap-6">
                    <div className="pb-4 border-b border-white/[0.06]">
                      <h3 className="text-xl font-bold text-white truncate">{cand.name}</h3>
                      <p className="text-sm text-indigo-300/80 mt-1 truncate">{cand.current_title || cand.headline}</p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">{cand.current_company} • {cand.location}</p>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Overall Match</div>
                        <div className={`text-sm font-bold uppercase tracking-wider px-2 py-1 rounded border inline-block ${getMatchTierColor(cand.overall_score)}`}>
                          {getMatchTier(cand.overall_score)} ({scorePercent(cand.overall_score)}%)
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Skill Match</div>
                        <div className="text-sm font-medium text-slate-200">
                          {scorePercent(cand.skill_fit_percent)}% • {cand.matched_skills?.length || 0} matched
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Semantic Match</div>
                        <div className="text-sm font-medium text-slate-200">
                          {cand.semantic_fit_percent}% contextual alignment
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Experience</div>
                        <div className="text-sm font-medium text-slate-200">
                          {cand.years_of_experience} years
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Role Alignment</div>
                        <div className="text-sm font-medium text-slate-200">
                          {cand.role_fit_percent}% fit
                        </div>
                      </div>

                      {cand.missing_skills && cand.missing_skills.length > 0 && (
                        <div>
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Missing Skills</div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {cand.missing_skills.map((skill) => (
                              <span key={skill} className="px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px]">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
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
