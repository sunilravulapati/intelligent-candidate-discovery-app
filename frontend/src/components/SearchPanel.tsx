"use client";

import React, { useState } from "react";

interface SearchPanelProps {
  onSearch: (title: string, description: string, skills: string[]) => void;
  isLoading: boolean;
}

export default function SearchPanel({ onSearch, isLoading }: SearchPanelProps) {
  const [title, setTitle] = useState("Backend Engineer");
  const [description, setDescription] = useState(
    "We are looking for a backend engineer experienced in building scalable web APIs. The candidate should be proficient in Python, FastAPI, and PostgreSQL. Experience with FAISS, search algorithms, and vector embeddings is a strong plus."
  );
  const [skillsText, setSkillsText] = useState("Python, FastAPI, PostgreSQL, FAISS");

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
    <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden group">
      {/* Glow Effect */}
      <div className="absolute -inset-px bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl blur opacity-30 group-hover:opacity-50 transition duration-1000" />
      
      <div className="relative">
        <h2 className="text-xl font-semibold text-slate-100 mb-6 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Search Candidates
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="job-title-input" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Job Title
            </label>
            <input
              id="job-title-input"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Lead Machine Learning Engineer"
              required
              className="w-full bg-slate-950/80 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
            />
          </div>

          <div>
            <label htmlFor="job-desc-input" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Job Description
            </label>
            <textarea
              id="job-desc-input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe candidate requirements, experience, and responsibilities..."
              required
              rows={5}
              className="w-full bg-slate-950/80 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all resize-none text-sm leading-relaxed"
            />
          </div>

          <div>
            <label htmlFor="skills-input" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Required Skills (Comma separated)
            </label>
            <input
              id="skills-input"
              type="text"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              placeholder="e.g. Python, FAISS, PyTorch"
              className="w-full bg-slate-950/80 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
            />
          </div>

          <button
            id="find-candidates-button"
            type="submit"
            disabled={isLoading}
            className={`w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium py-3.5 px-4 rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/35 transition-all flex items-center justify-center gap-2 group-hover:scale-[1.01] duration-300 disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Processing Model Features...
              </>
            ) : (
              <>
                <span>Find Candidates</span>
                <svg className="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
