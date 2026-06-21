"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";

interface CandidateDetailProps {
  candidate: CandidateMatch | null;
}

export default function CandidateDetail({ candidate }: CandidateDetailProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "experience" | "skills" | "signals">("overview");

  if (!candidate) {
    return (
      <div className="h-full bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl flex flex-col items-center justify-center text-center p-8 shadow-2xl">
        <div className="w-16 h-16 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-center mb-4 text-slate-600">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <p className="text-slate-400 font-semibold text-base">Select a Candidate</p>
        <p className="text-slate-600 text-xs mt-1.5 max-w-xs leading-relaxed">
          Choose a candidate from the left list to instantly view their complete profile, skills overlap, and matching explanation.
        </p>
      </div>
    );
  }

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
    if (score >= 0.75) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/5";
    if (score >= 0.55) return "text-indigo-400 border-indigo-500/20 bg-indigo-500/5";
    if (score >= 0.35) return "text-amber-400 border-amber-500/20 bg-amber-500/5";
    return "text-slate-400 border-slate-500/20 bg-slate-500/5";
  };

  const getScoreProgressColor = (score: number) => {
    if (score >= 0.75) return "bg-gradient-to-r from-emerald-500 to-teal-500";
    if (score >= 0.55) return "bg-gradient-to-r from-indigo-500 to-purple-500";
    if (score >= 0.35) return "bg-gradient-to-r from-amber-500 to-orange-500";
    return "bg-slate-500";
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
      {/* Detail Header */}
      <div className="p-5 border-b border-slate-800/80 bg-slate-950/40 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-4 select-none">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h2 className="text-lg font-bold text-slate-100">{candidate.name}</h2>
            <span className="text-[9px] text-slate-500 font-mono bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
              {candidate.candidate_id}
            </span>
          </div>
          <p className="text-xs text-indigo-300 font-semibold">{candidate.headline}</p>
          <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-1 font-medium">
            <span className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              {candidate.current_company || "No Company"}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {candidate.years_of_experience} Years Experience
            </span>
          </div>
        </div>

        {/* Header Scores Ring */}
        <div className="flex items-center gap-2">
          {/* Overall */}
          <div className={`border rounded-xl px-3 py-2 flex flex-col items-center justify-center text-center w-20 ${getScoreColor(candidate.overall_score)}`}>
            <span className="text-[9px] uppercase tracking-wider font-extrabold opacity-60">Overall</span>
            <span className="text-sm font-black font-mono mt-0.5">{(candidate.overall_score * 100).toFixed(0)}%</span>
          </div>
          {/* Semantic */}
          <div className="border border-violet-500/20 bg-violet-500/5 text-violet-400 rounded-xl px-3 py-2 flex flex-col items-center justify-center text-center w-20">
            <span className="text-[9px] uppercase tracking-wider font-extrabold opacity-60">Semantic</span>
            <span className="text-sm font-black font-mono mt-0.5">{candidate.semantic_similarity_percent}%</span>
          </div>
          {/* Skills */}
          <div className="border border-purple-500/20 bg-purple-500/5 text-purple-400 rounded-xl px-3 py-2 flex flex-col items-center justify-center text-center w-20">
            <span className="text-[9px] uppercase tracking-wider font-extrabold opacity-60">Skills</span>
            <span className="text-sm font-black font-mono mt-0.5">{candidate.skills_match_percent}%</span>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="flex border-b border-slate-800 bg-slate-900/20 px-4 shrink-0 select-none">
        {(["overview", "experience", "skills", "signals"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-3.5 px-4 text-[10px] font-extrabold uppercase tracking-wider border-b-2 transition duration-200 -mb-px ${
              activeTab === tab
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab === "overview" ? "Overview" :
             tab === "experience" ? "Career" :
             tab === "skills" ? "Skills" : "Signals"}
          </button>
        ))}
      </div>

      {/* Tab Content Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar">
        {/* Tab 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-5">
            {/* Match explanation narrative */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4.5 space-y-3">
              <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 select-none">
                <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                AI Sourcing Explanation
              </h3>
              <p className="text-slate-300 text-xs leading-relaxed whitespace-pre-line font-light">
                {reason}
              </p>
            </div>

            {/* Skills overlap breakdown */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4.5 space-y-4">
              <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 select-none">
                <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9-1V4a1 1 0 00-1-1h-2a1 1 0 00-1 1v14a1 1 0 001 1h2a1 1 0 001-1z" />
                </svg>
                Required Skills Match
              </h3>

              <div className="space-y-4">
                {/* Matched */}
                <div>
                  <div className="flex justify-between text-[11px] font-bold text-slate-400 mb-2 select-none">
                    <span>Matched required skills</span>
                    <span className="text-emerald-400">{matched.length} Matched</span>
                  </div>
                  {matched.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {matched.map((skill, idx) => (
                        <span
                          key={idx}
                          className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] px-2.5 py-1 rounded-lg flex items-center gap-1 font-medium font-mono"
                        >
                          <svg className="w-2.5 h-2.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-500 italic select-none">No matched required skills found in profile.</p>
                  )}
                </div>

                {/* Missing */}
                <div>
                  <div className="flex justify-between text-[11px] font-bold text-slate-400 mb-2 select-none">
                    <span>Missing required skills</span>
                    <span className="text-rose-400">{missing.length} Missing</span>
                  </div>
                  {missing.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {missing.map((skill, idx) => (
                        <span
                          key={idx}
                          className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] px-2.5 py-1 rounded-lg flex items-center gap-1 font-medium font-mono"
                        >
                          <svg className="w-2.5 h-2.5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-500 italic select-none">No missing required skills.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: EXPERIENCE */}
        {activeTab === "experience" && (
          <div className="space-y-4">
            <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider select-none">Career History Timeline</h3>
            {candidate.career_history.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">No career history listed in profile.</div>
            ) : (
              <div className="relative border-l border-slate-800 ml-3 pl-5 space-y-4">
                {candidate.career_history.map((exp, idx) => (
                  <div key={idx} className="relative group">
                    {/* Timeline dot */}
                    <span className="absolute -left-[27px] top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-slate-950 border border-slate-700 group-hover:border-indigo-500 transition-colors">
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-700 group-hover:bg-indigo-500 transition-colors" />
                    </span>

                    <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 hover:border-slate-700/60 transition duration-150">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <div>
                          <h4 className="font-bold text-slate-200 text-xs leading-tight">{exp.title}</h4>
                          <p className="text-[11px] text-indigo-400 font-semibold mt-0.5">{exp.company}</p>
                        </div>
                        <div className="sm:text-right">
                          <span className="bg-slate-900 border border-slate-800 text-[9px] text-slate-400 px-1.5 py-0.5 rounded font-mono whitespace-nowrap">
                            {exp.start_date} to {exp.end_date || "Present"}
                          </span>
                          <p className="text-[9px] text-slate-500 mt-1 font-semibold">
                            {Math.floor(exp.duration_months / 12) > 0 ? `${Math.floor(exp.duration_months / 12)}y ` : ""}
                            {exp.duration_months % 12 > 0 ? `${exp.duration_months % 12}m` : ""}
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-slate-500 uppercase tracking-widest mt-2.5 font-bold select-none">
                        <span>Industry: {exp.industry}</span>
                        <span>•</span>
                        <span>Company Size: {exp.company_size}</span>
                      </div>

                      <p className="text-slate-400 text-xs mt-2.5 leading-relaxed font-light whitespace-pre-line border-t border-slate-800/40 pt-2">
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
          <div className="space-y-4">
            <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider select-none">Full Skill Profile</h3>
            {candidate.skills.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">No skills listed in profile.</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {candidate.skills.map((skill, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-between hover:border-slate-700/60 transition duration-150"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <span className="font-bold text-slate-200 text-xs truncate pr-1">{skill.name}</span>
                      <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider shrink-0 ${
                        skill.proficiency === "expert" ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" :
                        skill.proficiency === "advanced" ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" :
                        skill.proficiency === "intermediate" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                        "bg-slate-850 text-slate-400 border border-slate-800"
                      }`}>
                        {skill.proficiency}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 mt-3 font-semibold select-none">
                      <span>Duration: {skill.duration_months} mos</span>
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          <div className="space-y-4">
            {/* Completeness bar */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4.5">
              <div className="flex justify-between items-center mb-2 select-none">
                <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Engagement & completeness</h3>
                <span className="text-[11px] font-bold text-indigo-400 font-mono">
                  {candidate.redrob_signals.profile_completeness_score}% Complete
                </span>
              </div>
              <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                  style={{ width: `${candidate.redrob_signals.profile_completeness_score}%` }}
                />
              </div>
            </div>

            {/* Sourcing details grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Job Seek Status</span>
                <div className="mt-1 flex items-center gap-1.5">
                  {candidate.redrob_signals.open_to_work_flag ? (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs font-bold text-emerald-400">Open to Work</span>
                    </>
                  ) : (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
                      <span className="text-xs font-bold text-slate-400">Passive Sourcing</span>
                    </>
                  )}
                </div>
              </div>

              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Expected Salary</span>
                <span className="text-xs font-bold text-slate-300 mt-1 font-mono">
                  {candidate.redrob_signals.expected_salary_range_inr_lpa.min} - {candidate.redrob_signals.expected_salary_range_inr_lpa.max} LPA
                </span>
              </div>

              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Notice Period</span>
                <span className="text-xs font-bold text-slate-300 mt-1 font-mono">
                  {candidate.redrob_signals.notice_period_days} Days
                </span>
              </div>

              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Github Sourcing</span>
                <div className="text-xs font-bold text-slate-300 mt-1 flex items-center gap-1.5 font-mono">
                  <span className={`h-1.5 w-1.5 rounded-full ${
                    candidate.redrob_signals.github_activity_score > 70 ? "bg-emerald-500" :
                    candidate.redrob_signals.github_activity_score > 30 ? "bg-amber-500" :
                    candidate.redrob_signals.github_activity_score >= 0 ? "bg-rose-500" : "bg-slate-600"
                  }`} />
                  <span>
                    {candidate.redrob_signals.github_activity_score >= 0 
                      ? `${candidate.redrob_signals.github_activity_score}/100` 
                      : "No Account"}
                  </span>
                </div>
              </div>

              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Work Mode</span>
                <span className="text-xs font-bold text-slate-300 mt-1 capitalize">
                  {candidate.redrob_signals.preferred_work_mode}
                </span>
              </div>

              <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-center">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-slate-500 select-none">Relocation</span>
                <span className="text-xs font-bold text-slate-300 mt-1">
                  {candidate.redrob_signals.willing_to_relocate ? "Willing" : "Not Sourced"}
                </span>
              </div>
            </div>

            {/* Sourcing funnel */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4.5 space-y-3.5">
              <h4 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider select-none">ATS Interaction Metrics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-0.5">
                  <div className="text-[10px] text-slate-500 font-bold select-none">Recruiter Views (30 Days)</div>
                  <div className="text-sm font-semibold text-slate-300 font-mono">
                    {candidate.redrob_signals.profile_views_received_30d} views
                  </div>
                </div>
                <div className="space-y-0.5">
                  <div className="text-[10px] text-slate-500 font-bold select-none">Active Applications</div>
                  <div className="text-sm font-semibold text-slate-300 font-mono">
                    {candidate.redrob_signals.applications_submitted_30d} roles
                  </div>
                </div>
                <div className="space-y-0.5">
                  <div className="text-[10px] text-slate-500 font-bold select-none">Recruiter Response Rate</div>
                  <div className="text-sm font-semibold text-slate-300 font-mono">
                    {(candidate.redrob_signals.recruiter_response_rate * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="space-y-0.5">
                  <div className="text-[10px] text-slate-500 font-bold select-none">Network Connections</div>
                  <div className="text-sm font-semibold text-slate-300 font-mono">
                    {candidate.redrob_signals.connection_count}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
