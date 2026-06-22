"use client";

import React from "react";

interface SearchPanelProps {
  onSearch: (title: string, description: string, skills: string[]) => void;
  isLoading: boolean;
  disabled?: boolean;
  title: string;
  description: string;
  skillsText: string;
  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onSkillsTextChange: (value: string) => void;
}

export default function SearchPanel({
  onSearch,
  isLoading,
  disabled = false,
  title,
  description,
  skillsText,
  onTitleChange,
  onDescriptionChange,
  onSkillsTextChange,
}: SearchPanelProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    const skillsList = skillsText
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    onSearch(title, description, skillsList);
  };

  return (
    <div className="bg-white/[0.03] backdrop-blur-2xl border border-white/[0.06] rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.2)] relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.05] to-transparent pointer-events-none" />

      <div className="relative">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white tracking-tight">New Search</h2>
          <p className="text-xs text-slate-500 mt-1">Define role requirements to build your shortlist</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="job-title-input" className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Role Title
            </label>
            <input
              id="job-title-input"
              type="text"
              value={title}
              onChange={(e) => onTitleChange(e.target.value)}
              placeholder="e.g. Backend Engineer"
              required
              className="w-full bg-slate-950/60 border border-white/[0.08] focus:border-indigo-500/50 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
            />
          </div>

          <div>
            <label htmlFor="job-desc-input" className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Job Description
            </label>
            <textarea
              id="job-desc-input"
              value={description}
              onChange={(e) => onDescriptionChange(e.target.value)}
              placeholder="Describe responsibilities, team context, and ideal background…"
              required
              rows={5}
              className="w-full bg-slate-950/60 border border-white/[0.08] focus:border-indigo-500/50 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all resize-none leading-relaxed"
            />
          </div>

          <div>
            <label htmlFor="skills-input" className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Required Skills
            </label>
            <input
              id="skills-input"
              type="text"
              value={skillsText}
              onChange={(e) => onSkillsTextChange(e.target.value)}
              placeholder="Python, FastAPI, PostgreSQL, FAISS"
              className="w-full bg-slate-950/60 border border-white/[0.08] focus:border-indigo-500/50 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
            />
            <p className="text-[10px] text-slate-600 mt-1.5">Comma-separated list</p>
          </div>

          <button
            id="find-candidates-button"
            type="submit"
            disabled={isLoading || disabled}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3.5 px-4 rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-sm"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span key={i} className="w-1.5 h-1.5 rounded-full bg-white/80 animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </span>
                Searching…
              </span>
            ) : (
              <>
                <span>Search Candidates</span>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
