"use client";

import React from "react";
import { SearchMetrics } from "@/lib/api";

interface SearchSummaryHeaderProps {
  queryTitle: string;
  queryDescription: string;
  querySkills: string[];
  metrics: SearchMetrics | null;
  resultCount: number;
  onRefine: () => void;
}

export default function SearchSummaryHeader({
  queryTitle,
  queryDescription,
  querySkills,
  metrics,
  resultCount,
  onRefine,
}: SearchSummaryHeaderProps) {
  const retrievalLabel =
    metrics?.retrieval_mode === "semantic"
      ? "Semantic Retrieval"
      : metrics?.retrieval_mode === "keyword"
      ? "Keyword Retrieval"
      : "Retrieval";

  return (
    <div className="bg-white/[0.03] backdrop-blur-2xl border border-white/[0.06] rounded-2xl px-6 py-5 shadow-[0_8px_32px_rgba(0,0,0,0.24)] relative overflow-hidden shrink-0">
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/[0.04] via-transparent to-violet-500/[0.04] pointer-events-none" />

      <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        <div className="flex-1 min-w-0 space-y-3">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-xl font-semibold text-white tracking-tight">
              {queryTitle || "Search Results"}
            </h2>
            {metrics && (
              <span
                className={`text-[10px] font-semibold uppercase tracking-widest px-2.5 py-1 rounded-full border ${
                  metrics.retrieval_mode === "semantic"
                    ? "bg-violet-500/10 text-violet-300 border-violet-500/25"
                    : "bg-amber-500/10 text-amber-300 border-amber-500/25"
                }`}
              >
                {retrievalLabel}
              </span>
            )}
          </div>

          <p className="text-sm text-slate-400 leading-relaxed line-clamp-2 max-w-3xl">
            {queryDescription}
          </p>

          {querySkills.length > 0 ? (
            <div className="flex flex-wrap items-center gap-x-1 gap-y-1 text-sm text-slate-400">
              {querySkills.map((skill, idx) => (
                <React.Fragment key={skill + idx}>
                  {idx > 0 && <span className="text-slate-600 mx-0.5">•</span>}
                  <span className="text-slate-300">{skill}</span>
                </React.Fragment>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic">No explicit required skills</p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {metrics && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <div className="flex flex-col items-end px-3 py-2 rounded-xl bg-slate-950/50 border border-white/[0.05]">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                  Indexed
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {metrics.candidates_indexed.toLocaleString()}
                </span>
              </div>
              <div className="flex flex-col items-end px-3 py-2 rounded-xl bg-slate-950/50 border border-white/[0.05]">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                  Retrieved
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {resultCount} ranked
                </span>
              </div>
              <div className="flex flex-col items-end px-3 py-2 rounded-xl bg-slate-950/50 border border-white/[0.05]">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                  Query Time
                </span>
                <span className="font-semibold text-emerald-400 tabular-nums">
                  {metrics.total_time_ms}ms
                </span>
              </div>
            </div>
          )}

          <button
            onClick={onRefine}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-300 bg-slate-950/60 border border-white/[0.08] hover:border-indigo-500/40 hover:text-white transition-all cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Refine Search
          </button>
        </div>
      </div>
    </div>
  );
}
