"use client";

import React from "react";
import { SearchMetrics } from "@/lib/api";

interface AnalyticsCardsProps {
  metrics: SearchMetrics | null;
}

export default function AnalyticsCards({ metrics }: AnalyticsCardsProps) {
  // Safe fallbacks if metrics is null (e.g. before search)
  const stats = [
    {
      id: "stat-candidates-indexed",
      name: "Candidates Indexed",
      value: metrics ? metrics.candidates_indexed.toLocaleString() : "--",
      sub: metrics?.retrieval_pool_size ? `${metrics.retrieval_pool_size.toLocaleString()} in pool` : null,
      icon: (
        <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      bgGlow: "from-indigo-500/10 to-indigo-500/0",
      borderColor: "group-hover:border-indigo-500/30"
    },
    {
      id: "stat-avg-match-score",
      name: "Avg Match Score",
      value: metrics ? `${Math.round(metrics.avg_match_score * 100)}%` : "--",
      sub: metrics?.retrieval_mode ? metrics.retrieval_mode : null,
      icon: (
        <svg className="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9-1V4a1 1 0 00-1-1h-2a1 1 0 00-1 1v14a1 1 0 001 1h2a1 1 0 001-1z" />
        </svg>
      ),
      bgGlow: "from-purple-500/10 to-purple-500/0",
      borderColor: "group-hover:border-purple-500/30"
    },
    {
      id: "stat-retrieval-time",
      name: "Retrieval Time",
      value: metrics ? `${metrics.retrieval_time_ms} ms` : "--",
      sub: metrics?.ranking_time_ms ? `+${metrics.ranking_time_ms}ms rank` : null,
      icon: (
        <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      bgGlow: "from-amber-500/10 to-amber-500/0",
      borderColor: "group-hover:border-amber-500/30"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {stats.map((stat) => (
        <div 
          key={stat.id}
          id={stat.id}
          className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 shadow-xl relative overflow-hidden group transition duration-300"
        >
          {/* Subtle Glow */}
          <div className={`absolute inset-0 bg-gradient-to-br ${stat.bgGlow} opacity-30 group-hover:opacity-50 transition duration-500`} />
          
          <div className="relative flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
                {stat.name}
              </p>
              <h3 className="text-2xl font-bold text-slate-100 font-mono tracking-tight">
                {stat.value}
              </h3>
              {stat.sub && (
                <p className="text-[10px] text-slate-500 mt-0.5 uppercase tracking-wider">{stat.sub}</p>
              )}
            </div>
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
              {stat.icon}
            </div>
          </div>
        </div>
      ))}

      {/* Top Skills Card */}
      <div 
        id="stat-top-skills"
        className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 shadow-xl relative overflow-hidden group transition duration-300 md:col-span-1"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-emerald-500/0 opacity-30 group-hover:opacity-50 transition duration-500" />
        
        <div className="relative">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            Top Skills Found
          </p>
          {metrics && metrics.top_skills_found && metrics.top_skills_found.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {metrics.top_skills_found.map((skill, index) => (
                <span 
                  key={index}
                  className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold px-2 py-0.5 rounded"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-slate-600 text-xs py-1">
              Waiting for query...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
