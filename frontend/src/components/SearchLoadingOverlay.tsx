"use client";

import React, { useEffect, useState } from "react";

const PHASES = [
  "Generating Embeddings",
  "Searching Candidate Index",
  "Ranking Candidates",
  "Generating Match Insights",
];

interface SearchLoadingOverlayProps {
  isLoading: boolean;
}

export default function SearchLoadingOverlay({ isLoading }: SearchLoadingOverlayProps) {
  const [phaseIndex, setPhaseIndex] = useState(0);

  if (!isLoading && phaseIndex !== 0) {
    setPhaseIndex(0);
  }

  useEffect(() => {
    if (!isLoading) return;
    const interval = setInterval(() => {
      setPhaseIndex((i) => Math.min(i + 1, PHASES.length - 1));
    }, 1200);
    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
      <div className="max-w-md w-full mx-4 p-8 rounded-2xl bg-slate-900/90 border border-white/[0.08] shadow-[0_18px_70px_rgba(0,0,0,0.5)]">
        <h3 className="text-lg font-bold text-white mb-6 text-center tracking-tight">Analyzing Candidates</h3>
        
        <div className="space-y-4">
          {PHASES.map((phase, idx) => {
            const isActive = idx === phaseIndex;
            const isCompleted = idx < phaseIndex;
            return (
              <div key={phase} className="flex items-center gap-4">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border ${
                  isCompleted
                    ? "bg-emerald-500 border-emerald-500 text-white"
                    : isActive
                    ? "border-indigo-500 bg-indigo-500/10"
                    : "border-slate-700 bg-slate-800"
                }`}>
                  {isCompleted ? (
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : isActive ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                  ) : (
                    <span className="w-1 h-1 rounded-full bg-slate-600" />
                  )}
                </div>
                <span className={`text-sm font-medium ${
                  isCompleted ? "text-slate-400" : isActive ? "text-slate-200" : "text-slate-600"
                }`}>
                  {phase}
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-8 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${((phaseIndex + 1) / PHASES.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
