"use client";

import React, { useEffect, useState } from "react";

const PHASES = [
  "Building candidate shortlist…",
  "Running semantic retrieval…",
  "Ranking candidates by role & skill fit…",
];

interface SearchLoadingOverlayProps {
  isLoading: boolean;
}

export default function SearchLoadingOverlay({ isLoading }: SearchLoadingOverlayProps) {
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      return;
    }
    const resetTimer = setTimeout(() => setPhaseIndex(0), 0);
    const interval = setInterval(() => {
      setPhaseIndex((i) => (i + 1) % PHASES.length);
    }, 1200);
    return () => {
      clearTimeout(resetTimer);
      clearInterval(interval);
    };
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
      <div className="max-w-sm w-full mx-4 p-8 rounded-2xl bg-slate-900/90 border border-white/[0.08] shadow-2xl text-center">
        <div className="flex justify-center gap-1.5 mb-6">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className={`w-2 h-2 rounded-full transition-all duration-500 ${
                i <= phaseIndex ? "bg-indigo-400 scale-110" : "bg-slate-700"
              }`}
            />
          ))}
        </div>
        <p className="text-sm font-medium text-slate-200 transition-opacity duration-300">
          {PHASES[phaseIndex]}
        </p>
        <div className="mt-4 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${((phaseIndex + 1) / PHASES.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
