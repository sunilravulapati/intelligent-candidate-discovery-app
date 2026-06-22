"use client";

import React from "react";
import { SearchMetrics } from "@/lib/api";

interface AnalyticsCardsProps {
  metrics: SearchMetrics | null;
  hasSearched?: boolean;
}

export default function AnalyticsCards({ metrics, hasSearched = false }: AnalyticsCardsProps) {
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
      label: "Candidates Retrieved",
      value: metrics.retrieval_pool_size.toLocaleString(),
      sub: `${metrics.candidates_indexed.toLocaleString()} indexed`,
    },
    {
      label: "Average Match Score",
      value: `${Math.round(metrics.avg_match_score * 100)}%`,
      sub: metrics.retrieval_mode === "semantic" ? "Semantic mode" : "Keyword mode",
    },
    {
      label: "End-to-End Search",
      value: `${metrics.total_time_ms}ms`,
      sub: `Embedding ${embeddingMs}ms (${cacheState})`,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-xl px-5 py-4"
        >
          <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">{stat.label}</p>
          <p className="text-2xl font-bold text-white tabular-nums mt-1 tracking-tight">{stat.value}</p>
          <p className="text-[10px] text-slate-600 mt-0.5">{stat.sub}</p>
        </div>
      ))}

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-xl px-5 py-4">
        <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Pipeline Timing</p>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-2 text-[10px]">
          <div className="flex justify-between gap-2">
            <span className="text-slate-500">Embedding</span>
            <span className="text-slate-200 tabular-nums">{embeddingMs}ms</span>
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-slate-500">FAISS</span>
            <span className="text-slate-200 tabular-nums">{faissMs}ms</span>
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-slate-500">Ranking</span>
            <span className="text-slate-200 tabular-nums">{rankingMs}ms</span>
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-slate-500">Explain</span>
            <span className="text-slate-200 tabular-nums">{explainabilityMs}ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}
