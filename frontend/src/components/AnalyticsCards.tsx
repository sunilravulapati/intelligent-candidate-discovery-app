"use client";

import React from "react";
import { SearchMetrics, generateSubmission } from "@/lib/api";

interface AnalyticsCardsProps {
  metrics: SearchMetrics | null;
  hasSearched?: boolean;
  bestScore?: number;
  queryTitle?: string;
  queryDescription?: string;
  querySkills?: string[];
}

export default function AnalyticsCards({
  metrics,
  hasSearched = false,
  bestScore = 0,
  queryTitle = "",
  queryDescription = "",
  querySkills = [],
}: AnalyticsCardsProps) {
  if (!hasSearched || !metrics?.retrieval_pool_size) {
    return null;
  }

  const timing = metrics.timing_breakdown ?? {};
  const embeddingMs = metrics.embedding_time_ms ?? Math.round(timing["Query Embedding"] ?? 0);
  const faissMs = metrics.faiss_time_ms ?? Math.round(timing["FAISS Retrieval"] ?? 0);
  const rankingMs = metrics.ranking_time_ms ?? Math.round(timing["Candidate Ranking"] ?? 0);
  const explainabilityMs = metrics.explainability_time_ms ?? Math.round(timing["Explainability Generation"] ?? 0);
  const cacheState = metrics.embedding_cache_hit ? "cache hit" : "cache miss";

  const stats = [
    {
      label: "Talent Pool Evaluated",
      value: metrics.retrieval_pool_size.toLocaleString(),
      sub: `From pool of ${metrics.candidates_indexed.toLocaleString()}`,
    },
    {
      label: "Best Candidate Score",
      value: `${Math.round((bestScore || metrics.avg_match_score) * 100)}%`,
      sub: metrics.retrieval_mode === "semantic" ? "AI Semantic Search" : "Keyword Fallback",
    },
    {
      label: "Search Duration",
      value: `${metrics.total_time_ms}ms`,
      sub: "End-to-end execution",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-white/[0.08] bg-slate-900/40 p-5 shadow-lg shadow-black/20"
        >
          <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">{stat.label}</p>
          <p className="text-2xl font-bold text-white tabular-nums mt-1 tracking-tight">{stat.value}</p>
          <p className="text-[11px] text-indigo-300/80 mt-1 font-medium">{stat.sub}</p>
        </div>
      ))}

      <div className="rounded-xl border border-white/[0.08] bg-slate-900/40 p-5 shadow-lg shadow-black/20">
        <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-3">AI Ranking Pipeline</p>
        <div className="space-y-2 text-[11px] font-medium">
          <div className="flex justify-between items-center">
            <span className="text-slate-400 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-violet-500" />Embedding</span>
            <span className="text-slate-200 tabular-nums">{embeddingMs}ms <span className="text-slate-500 font-normal ml-1">({cacheState === "cache hit" ? "cached" : "computed"})</span></span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />Semantic Retrieval</span>
            <span className="text-slate-200 tabular-nums">{faissMs}ms</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-500" />Ranking</span>
            <span className="text-slate-200 tabular-nums">{rankingMs}ms</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />Insights</span>
            <span className="text-slate-200 tabular-nums">{explainabilityMs}ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}
