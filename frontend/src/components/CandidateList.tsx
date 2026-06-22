"use client";

import React from "react";
import { CandidateMatch } from "@/lib/api";
import { fitColorClass, rankBadgeClass, rankTone, scorePercent } from "@/lib/ranking";

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
  return (
    <div className="flex flex-col h-full bg-white/[0.025] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden shadow-[0_18px_70px_rgba(0,0,0,0.28)]">
      <div className="px-5 py-4 border-b border-white/[0.06] shrink-0">
        <h3 className="text-sm font-semibold text-white">Ranked Shortlist</h3>
        <p className="text-xs text-slate-500 mt-0.5">{candidates.length} candidates ranked by fit</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
        {candidates.map((cand) => {
          const isSelected = selectedCandidate?.candidate_id === cand.candidate_id;
          const rank = cand.rank;
          const isTop = rank === 1;

          return (
            <button
              key={cand.candidate_id}
              onClick={() => onSelectCandidate(cand)}
              className={`w-full text-left p-4 rounded-xl transition-all duration-200 cursor-pointer flex flex-col gap-3 relative ${
                isSelected
                  ? "bg-indigo-500/10 ring-1 ring-indigo-500/40 shadow-lg shadow-indigo-500/5"
                  : isTop
                  ? "bg-gradient-to-br from-amber-500/[0.06] to-transparent ring-1 ring-amber-500/20 hover:ring-amber-500/35"
                  : "bg-slate-900/30 hover:bg-slate-800/40 ring-1 ring-white/[0.04] hover:ring-white/[0.08]"
              }`}
            >
              {isSelected && (
                <div className="absolute left-0 top-3 bottom-3 w-0.5 bg-indigo-400 rounded-full" />
              )}

              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-black shrink-0 ${rankBadgeClass(rank)}`}>
                  #{rank}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className={`font-semibold text-sm truncate ${isTop ? "text-amber-50" : "text-slate-100"}`}>
                      {cand.name}
                    </div>
                    {rank <= 3 && (
                      <span className="text-[9px] uppercase tracking-wider text-slate-500 font-bold shrink-0">
                        {rankTone(rank)}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-indigo-300/90 font-medium truncate mt-0.5">
                    {cand.current_title || cand.headline}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate mt-0.5">
                    {cand.current_company} · {cand.years_of_experience} yrs
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className={`text-lg font-bold tabular-nums ${fitColorClass(scorePercent(cand.overall_score))}`}>
                    {scorePercent(cand.overall_score)}%
                  </div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-600 font-medium">Overall</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: "Role", value: cand.role_fit_percent },
                  { label: "Skills", value: cand.skill_fit_percent },
                  { label: "Semantic", value: cand.semantic_fit_percent },
                ].map((m) => (
                  <div key={m.label} className="rounded-lg bg-slate-950/50 py-1.5 px-1">
                    <div className={`text-xs font-semibold tabular-nums ${fitColorClass(m.value)}`}>{m.value}%</div>
                    <div className="text-[9px] text-slate-600 uppercase tracking-wide">{m.label}</div>
                  </div>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
