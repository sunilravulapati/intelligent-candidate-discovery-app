"use client";

import React, { useEffect, useState } from "react";
import { CandidateMatch, Skill, Experience, ActivitySignals } from "@/lib/api";

interface CandidateDrawerProps {
  candidate: CandidateMatch | null;
  onClose: () => void;
  isOpen: boolean;
}

export default function CandidateDrawer({ candidate, onClose, isOpen }: CandidateDrawerProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "experience" | "skills" | "signals">("overview");

  // Prevent scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!candidate) return null;

  // Parse structured explanation
  const parseExplanation = (explanation: string) => {
    const matchedMatch = explanation.match(/Matched:\s*([\s\S]*?)(?=\n\nMissing:|$)/);
    const missingMatch = explanation.match(/Missing:\s*([\s\S]*?)(?=\n\nReason:|$)/);
    const reasonMatch = explanation.match(/Reason:\s*([\s\S]*)$/);

    const matched = matchedMatch ? matchedMatch[1].trim().split(/,\s*/).filter(Boolean) : [];
    const missing = missingMatch ? missingMatch[1].trim().split(/,\s*/).filter(Boolean) : [];
    const reason = reasonMatch ? reasonMatch[1].trim() : explanation;

    return { matched, missing, reason };
  };

  const { matched, missing, reason } = parseExplanation(candidate.explanation);

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/5";
    if (score >= 0.7) return "text-indigo-400 border-indigo-500/20 bg-indigo-500/5";
    if (score >= 0.5) return "text-amber-400 border-amber-500/20 bg-amber-500/5";
    return "text-slate-400 border-slate-500/20 bg-slate-500/5";
  };

  const getScoreProgressColor = (score: number) => {
    if (score >= 0.85) return "bg-gradient-to-r from-emerald-500 to-teal-500";
    if (score >= 0.7) return "bg-gradient-to-r from-indigo-500 to-purple-500";
    if (score >= 0.5) return "bg-gradient-to-r from-amber-500 to-orange-500";
    return "bg-slate-500";
  };

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className={`fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed inset-y-0 right-0 z-50 w-full max-w-2xl bg-slate-950 border-l border-slate-800/80 shadow-2xl flex flex-col transition-transform duration-300 transform ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-900/30 flex items-start justify-between">
          <div className="space-y-1 pr-6">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-100">{candidate.name}</h2>
              <span className="text-[10px] text-slate-500 font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                {candidate.candidate_id}
              </span>
            </div>
            <p className="text-sm text-slate-400 font-medium">{candidate.headline}</p>
            <div className="flex items-center gap-4 text-xs text-slate-500 mt-2">
              <span className="flex items-center gap-1">
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                {candidate.current_company}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {candidate.years_of_experience} Years Experience
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 p-2 rounded-xl transition duration-150"
            aria-label="Close drawer"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-900/10 px-4">
          {(["overview", "experience", "skills", "signals"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 px-4 text-xs font-semibold uppercase tracking-wider border-b-2 transition duration-200 -mb-px ${
                activeTab === tab
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Tab 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Top Score Cards — 3-column grid */}
              <div className="grid grid-cols-3 gap-3">
                {/* Overall / Hybrid Score */}
                <div className={`border rounded-2xl p-4 flex flex-col items-center justify-center text-center ${getScoreColor(candidate.overall_score ?? candidate.match_score)}`}>
                  <div className="text-[10px] uppercase tracking-wider font-semibold opacity-70 mb-1">Overall</div>
                  <div className="text-2xl font-black font-mono">{((candidate.overall_score ?? candidate.match_score) * 100).toFixed(0)}%</div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3 max-w-[100px]">
                    <div
                      className={`h-full rounded-full ${getScoreProgressColor(candidate.overall_score ?? candidate.match_score)}`}
                      style={{ width: `${(candidate.overall_score ?? candidate.match_score) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Semantic Match */}
                <div className="border border-violet-500/20 bg-violet-500/5 text-violet-400 rounded-2xl p-4 flex flex-col items-center justify-center text-center">
                  <div className="text-[10px] uppercase tracking-wider font-semibold opacity-70 mb-1">Semantic</div>
                  <div className="text-2xl font-black font-mono">{candidate.semantic_similarity_percent ?? 0}%</div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3 max-w-[100px]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-500"
                      style={{ width: `${candidate.semantic_similarity_percent ?? 0}%` }}
                    />
                  </div>
                </div>

                {/* Skills Match */}
                <div className="border border-indigo-500/20 bg-indigo-500/5 text-indigo-400 rounded-2xl p-4 flex flex-col items-center justify-center text-center">
                  <div className="text-[10px] uppercase tracking-wider font-semibold opacity-70 mb-1">Skills</div>
                  <div className="text-2xl font-black font-mono">{candidate.skills_match_percent}%</div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3 max-w-[100px]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                      style={{ width: `${candidate.skills_match_percent}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Match Explanation */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Match Insights & Ranking Explanation
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line font-light">
                  {reason}
                </p>
              </div>

              {/* Skill Overlap Breakdown */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9-1V4a1 1 0 00-1-1h-2a1 1 0 00-1 1v14a1 1 0 001 1h2a1 1 0 001-1z" />
                  </svg>
                  Required Skills Overlap Breakdown
                </h3>

                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-xs font-semibold text-slate-400 mb-1.5">
                      <span>Matched Required Skills</span>
                      <span className="text-emerald-400">{matched.length} Matched</span>
                    </div>
                    {matched.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {matched.map((skill, idx) => (
                          <span
                            key={idx}
                            className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2.5 py-1 rounded-lg flex items-center gap-1 font-medium"
                          >
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                            </svg>
                            {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No skills from request matched.</p>
                    )}
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold text-slate-400 mb-1.5">
                      <span>Missing Required Skills</span>
                      <span className="text-rose-400">{missing.length} Missing</span>
                    </div>
                    {missing.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {missing.map((skill, idx) => (
                          <span
                            key={idx}
                            className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs px-2.5 py-1 rounded-lg flex items-center gap-1 font-medium"
                          >
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No missing skills required for this job description.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: EXPERIENCE */}
          {activeTab === "experience" && (
            <div className="space-y-6">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Career History</h3>
              {candidate.career_history.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No work experience listed in profile.</div>
              ) : (
                <div className="relative border-l border-slate-800 ml-4 pl-6 space-y-6">
                  {candidate.career_history.map((exp, idx) => (
                    <div key={idx} className="relative group">
                      {/* Timeline dot */}
                      <span className="absolute -left-[31px] top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-slate-950 border border-slate-700 group-hover:border-indigo-500 transition-colors">
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-700 group-hover:bg-indigo-500 transition-colors" />
                      </span>

                      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition duration-150">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-slate-200 text-sm">{exp.title}</h4>
                            <p className="text-xs text-indigo-400 font-medium mt-0.5">{exp.company}</p>
                          </div>
                          <div className="text-right">
                            <span className="bg-slate-900 border border-slate-800 text-[10px] text-slate-400 px-2 py-0.5 rounded font-mono">
                              {exp.start_date} to {exp.end_date || "Present"}
                            </span>
                            <p className="text-[10px] text-slate-500 mt-1">
                              {Math.floor(exp.duration_months / 12) > 0 ? `${Math.floor(exp.duration_months / 12)}y ` : ""}
                              {exp.duration_months % 12 > 0 ? `${exp.duration_months % 12}m` : ""}
                            </p>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 uppercase tracking-wider mt-3 font-semibold">
                          <span>Industry: {exp.industry}</span>
                          <span>•</span>
                          <span>Company Size: {exp.company_size}</span>
                        </div>

                        <p className="text-slate-400 text-xs mt-3 leading-relaxed font-light whitespace-pre-line">
                          {exp.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 3: SKILLS */}
          {activeTab === "skills" && (
            <div className="space-y-6">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Complete Skill Profile</h3>
              {candidate.skills.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No skills listed in profile.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {candidate.skills.map((skill, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700/80 transition duration-150"
                    >
                      <div className="flex justify-between items-start">
                        <span className="font-semibold text-slate-200 text-sm truncate pr-2">{skill.name}</span>
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded tracking-wide ${
                          skill.proficiency === "expert" ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" :
                          skill.proficiency === "advanced" ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" :
                          skill.proficiency === "intermediate" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                          "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}>
                          {skill.proficiency}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-500 mt-4">
                        <span>Duration: {skill.duration_months} mos</span>
                        <span className="flex items-center gap-1">
                          <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.757a1 1 0 00.707-1.707l-5.414-5.414a1 1 0 00-.707-.293V3a1 1 0 00-1-1h-2a1 1 0 00-1 1v1.586a1 1 0 00-.293.707L4.293 8.293a1 1 0 00-.707 1.707H8.5V12M14 10V8H8.5v2M12 14v7m-3-3h6" />
                          </svg>
                          {skill.endorsements} endorsements
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 4: REDROB SIGNALS */}
          {activeTab === "signals" && (
            <div className="space-y-6">
              {/* Profile Completeness Gauge */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Engagement & Activity signals</h3>
                  <span className="text-xs font-semibold text-indigo-400">
                    Profile Completeness: {candidate.redrob_signals.profile_completeness_score}%
                  </span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                    style={{ width: `${candidate.redrob_signals.profile_completeness_score}%` }}
                  />
                </div>
              </div>

              {/* Status Signals Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Job Seek Status</div>
                  <div className="mt-1 flex items-center gap-1.5">
                    {candidate.redrob_signals.open_to_work_flag ? (
                      <>
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-sm font-semibold text-emerald-400">Open to Work</span>
                      </>
                    ) : (
                      <>
                        <span className="h-2 w-2 rounded-full bg-slate-600" />
                        <span className="text-sm font-semibold text-slate-400">Passive Sourcing</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Expected Salary</div>
                  <div className="text-sm font-semibold text-slate-300 mt-1">
                    {candidate.redrob_signals.expected_salary_range_inr_lpa.min} - {candidate.redrob_signals.expected_salary_range_inr_lpa.max} LPA
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Notice Period</div>
                  <div className="text-sm font-semibold text-slate-300 mt-1">
                    {candidate.redrob_signals.notice_period_days} Days
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">GitHub Activity</div>
                  <div className="text-sm font-semibold text-slate-300 mt-1 flex items-center gap-1.5">
                    <span className={`h-2 w-2 rounded-full ${
                      candidate.redrob_signals.github_activity_score > 70 ? "bg-emerald-500" :
                      candidate.redrob_signals.github_activity_score > 30 ? "bg-amber-500" :
                      candidate.redrob_signals.github_activity_score >= 0 ? "bg-rose-500" : "bg-slate-600"
                    }`} />
                    <span>
                      {candidate.redrob_signals.github_activity_score >= 0 
                        ? `${candidate.redrob_signals.github_activity_score}/100` 
                        : "No Profile Connected"}
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Work Mode</div>
                  <div className="text-sm font-semibold text-slate-300 mt-1 capitalize">
                    {candidate.redrob_signals.preferred_work_mode}
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Relocation</div>
                  <div className="text-sm font-semibold text-slate-300 mt-1">
                    {candidate.redrob_signals.willing_to_relocate ? "Willing" : "Not Willing"}
                  </div>
                </div>
              </div>

              {/* Engagement statistics */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Recruiter Sourcing Interactions</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <div className="text-[11px] text-slate-500">Profile Views (30 Days)</div>
                    <div className="text-lg font-semibold text-slate-200">
                      {candidate.redrob_signals.profile_views_received_30d} views
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-[11px] text-slate-500">Submitted Applications</div>
                    <div className="text-lg font-semibold text-slate-200">
                      {candidate.redrob_signals.applications_submitted_30d} roles
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-[11px] text-slate-500">Recruiter Response Rate</div>
                    <div className="text-lg font-semibold text-slate-200">
                      {(candidate.redrob_signals.recruiter_response_rate * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-[11px] text-slate-500">Connections count</div>
                    <div className="text-lg font-semibold text-slate-200">
                      {candidate.redrob_signals.connection_count}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
