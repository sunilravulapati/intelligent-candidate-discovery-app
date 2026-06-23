"use client";

import React, { useState } from "react";
import { CandidateMatch } from "@/lib/api";
import {
  RANKING_FORMULA,
  RANKING_FORMULA_HELP,
  RANKING_WEIGHTS,
  fitColorClass,
  rankBadgeClass,
  rankTone,
  scorePercent,
  getMatchTier,
  getMatchTierColor,
} from "@/lib/ranking";

interface CandidateDetailProps {
  candidate: CandidateMatch | null;
  queryTitle?: string;
}

import { useCandidateWorkflow, WorkflowAction } from "@/lib/workflow";
import { showToast } from "@/components/Toast";

function ScoreCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className={`flex-1 min-w-[88px] rounded-xl border px-3 py-3 text-center ${accent}`}>
      <div className="text-[10px] uppercase tracking-wider font-semibold opacity-70">{label}</div>
      <div className="text-lg font-bold tabular-nums mt-1">{value}</div>
    </div>
  );
}

export default function CandidateDetail({ candidate, queryTitle }: CandidateDetailProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "experience" | "skills" | "signals">("overview");
  const { workflowState, setWorkflowStatus } = useCandidateWorkflow();

  if (!candidate) {
    return (
      <div className="h-full bg-white/[0.02] backdrop-blur-xl border border-white/[0.06] rounded-2xl flex flex-col items-center justify-center text-center p-10">
        <div className="w-14 h-14 rounded-2xl bg-slate-900/80 border border-white/[0.06] flex items-center justify-center mb-4 text-slate-600">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <p className="text-slate-300 font-medium">Select a candidate</p>
        <p className="text-slate-600 text-sm mt-1.5 max-w-xs">
          Choose from the shortlist to view match breakdown, skills analysis, and career timeline.
        </p>
      </div>
    );
  }

  const matched = candidate.matched_skills ?? [];
  const missing = candidate.missing_skills ?? [];
  const currentWorkflow = workflowState[candidate.candidate_id];
  const setCandidateWorkflow = (status: WorkflowAction) => {
    const isActivating = currentWorkflow?.status !== status;
    setWorkflowStatus(candidate.candidate_id, status);
    
    if (isActivating) {
      if (status === "saved") showToast("✓ Candidate Saved", "success");
      else if (status === "shortlisted") showToast("✓ Added to Shortlist", "success");
      else if (status === "rejected") showToast("Candidate Rejected", "error");
    }
  };
  const requestedSkillCount = matched.length + missing.length;
  const generatedInsights = [
    candidate.role_fit_percent >= 80
      ? `Strong alignment with ${queryTitle || "role"} requirements.`
      : candidate.role_fit_percent >= 50
      ? `Moderate alignment with ${queryTitle || "role"} requirements.`
      : `Needs further evaluation for ${queryTitle || "role"} alignment.`,
    
    requestedSkillCount > 0
      ? `Matches ${matched.length} of ${requestedSkillCount} required technologies.`
      : "No specific technical constraints provided in query.",
      
    `${candidate.years_of_experience}+ years of relevant industry experience.`,
    
    candidate.semantic_fit_percent >= 80
      ? "High semantic similarity to the detailed role description."
      : candidate.semantic_fit_percent >= 50
      ? "Solid semantic overlap with core responsibilities."
      : "Baseline semantic match; recommend deeper interview screening."
  ];
  const reasons = candidate.ranking_reasons?.length ? candidate.ranking_reasons : generatedInsights;

  const breakdownBars = [
    { label: "Overall Score", pct: scorePercent(candidate.overall_score), weight: "Final", color: "from-white to-slate-300" },
    { label: "Semantic Score", pct: candidate.semantic_fit_percent, weight: `${RANKING_WEIGHTS.semantic}%`, color: "from-violet-500 to-purple-500" },
    { label: "Skill Match", pct: candidate.skill_fit_percent, weight: `${RANKING_WEIGHTS.skills}%`, color: "from-indigo-500 to-violet-500" },
    { label: "Experience Score", pct: scorePercent(candidate.experience_score), weight: `${RANKING_WEIGHTS.experience}%`, color: "from-cyan-500 to-blue-500" },
    { label: "Role Alignment", pct: candidate.role_fit_percent, weight: `${RANKING_WEIGHTS.role}%`, color: "from-emerald-500 to-teal-500" },
    { label: "Activity Signal", pct: scorePercent(candidate.activity_score), weight: `${RANKING_WEIGHTS.activity}%`, color: "from-amber-500 to-orange-500" },
  ];

  return (
    <div className="flex flex-col h-full bg-white/[0.02] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.2)]">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/[0.06] shrink-0 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full ${rankBadgeClass(candidate.rank)}`}>
                #{candidate.rank} {rankTone(candidate.rank)}
              </span>
              {candidate.rank === 1 && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400/90 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                  Top Match
                </span>
              )}
              <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getMatchTierColor(candidate.overall_score)}`}>
                {getMatchTier(candidate.overall_score)}
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white mt-2 tracking-tight">{candidate.name}</h2>
            <p className="text-sm text-indigo-300/90 font-medium mt-0.5">{candidate.current_title || candidate.headline}</p>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mt-2">
              <span>{candidate.current_company}</span>
              <span className="text-slate-700">·</span>
              <span>{candidate.years_of_experience} years experience</span>
            </div>
          </div>
          <div className="flex flex-wrap justify-end gap-2 shrink-0">
            {([
              { label: "Save", activeLabel: "Saved ✓", value: "saved" as WorkflowAction },
              { label: "Shortlist", activeLabel: "Shortlisted ✓", value: "shortlisted" as WorkflowAction },
              { label: "Reject", activeLabel: "Rejected ✓", value: "rejected" as WorkflowAction },
            ]).map((action) => {
              const active = currentWorkflow?.status === action.value;
              const activeClass =
                action.value === "rejected"
                  ? "border-rose-500/40 bg-rose-500/10 text-rose-200"
                  : action.value === "shortlisted"
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                  : "border-indigo-500/40 bg-indigo-500/10 text-indigo-200";
              return (
                <button
                  key={action.value}
                  type="button"
                  onClick={() => setCandidateWorkflow(action.value)}
                  className={`px-3 py-1.5 rounded-lg border text-[11px] font-semibold transition cursor-pointer ${
                    active
                      ? activeClass
                      : "border-white/[0.08] bg-slate-950/40 text-slate-400 hover:text-slate-100 hover:border-white/[0.16]"
                  }`}
                >
                  {active ? action.activeLabel : action.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-0.5">
          <ScoreCard label="Overall Match" value={`${scorePercent(candidate.overall_score)}%`} accent="border-indigo-500/25 bg-indigo-500/10 text-indigo-200" />
          <ScoreCard label="Role Alignment" value={`${candidate.role_fit_percent}%`} accent="border-emerald-500/25 bg-emerald-500/10 text-emerald-200" />
          <ScoreCard label="Skill Match" value={`${candidate.skill_fit_percent}%`} accent="border-violet-500/25 bg-violet-500/10 text-violet-200" />
          <ScoreCard label="Semantic" value={`${candidate.semantic_fit_percent}%`} accent="border-purple-500/25 bg-purple-500/10 text-purple-200" />
          <ScoreCard label="Experience" value={`${scorePercent(candidate.experience_score)}%`} accent="border-cyan-500/25 bg-cyan-500/10 text-cyan-200" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/[0.06] px-4 shrink-0">
        {(["overview", "experience", "skills", "signals"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-3 px-4 text-xs font-semibold capitalize border-b-2 transition -mb-px cursor-pointer ${
              activeTab === tab
                ? "border-indigo-400 text-indigo-300"
                : "border-transparent text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab === "experience" ? "Career" : tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {activeTab === "overview" && (
          <>
            {/* Why Selected */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                {candidate.rank === 1 ? "Why Ranked #1" : `Why Ranked #${candidate.rank}`}
              </h3>
              <ul className="space-y-2.5">
                {reasons.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <span className="text-emerald-400 mt-0.5 shrink-0">✓</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* Recruiter Actions */}
            {currentWorkflow && (
              <section className="rounded-xl border border-white/[0.06] bg-slate-950/30 p-4 space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Recruiter Actions
                </h3>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <span className={`w-2 h-2 rounded-full ${
                    currentWorkflow.status === "saved" ? "bg-indigo-400" :
                    currentWorkflow.status === "shortlisted" ? "bg-emerald-400" : "bg-rose-400"
                  }`} />
                  <span className="capitalize">{currentWorkflow.status}</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-500">
                    {new Date(currentWorkflow.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </section>
            )}

            {/* Ranking breakdown */}
            <section className="rounded-xl border border-white/[0.06] bg-slate-950/30 p-4 space-y-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Ranking Breakdown
                    {queryTitle && <span className="text-slate-600 font-normal normal-case ml-1">for {queryTitle}</span>}
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-1" title={RANKING_FORMULA_HELP}>
                    {RANKING_FORMULA}
                  </p>
                </div>
                <span
                  className="inline-flex w-fit items-center rounded-full border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400"
                  title={RANKING_FORMULA_HELP}
                >
                  Formula
                </span>
              </div>
              {breakdownBars.map((bar) => (
                <div key={bar.label} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">
                      {bar.label} <span className="text-slate-600">({bar.weight})</span>
                    </span>
                    <span className="text-slate-300 font-semibold tabular-nums">{bar.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${bar.color} rounded-full transition-all duration-500`}
                      style={{ width: `${Math.min(bar.pct, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </section>

            {/* Skills Analysis */}
            <section className="space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Skills Analysis</h3>

              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-xs font-semibold text-emerald-400">Matched Skills</span>
                  <span className="text-xs text-emerald-400/80 tabular-nums">{matched.length} matched · {candidate.skill_fit_percent}%</span>
                </div>
                {matched.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {matched.map((skill) => (
                      <span key={skill} className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/25 font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No required skills matched.</p>
                )}
              </div>

              <div className="rounded-xl border border-rose-500/20 bg-rose-500/[0.04] p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-xs font-semibold text-rose-400">Missing Skills</span>
                  <span className="text-xs text-rose-400/80 tabular-nums">{missing.length} missing</span>
                </div>
                {missing.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {missing.map((skill) => (
                      <span key={skill} className="text-xs px-2.5 py-1 rounded-lg bg-rose-500/15 text-rose-300 border border-rose-500/25 font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-emerald-400/80">All required skills matched.</p>
                )}
              </div>
            </section>
          </>
        )}

        {activeTab === "experience" && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Career Timeline</h3>
            {candidate.career_history.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">No career history available.</p>
            ) : (
              <div className="relative pl-6 space-y-0">
                <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gradient-to-b from-indigo-500/50 via-slate-700 to-transparent" />
                {candidate.career_history.map((exp, idx) => (
                  <div key={idx} className="relative pb-6 last:pb-0">
                    <div className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 ${
                      idx === 0 ? "bg-indigo-500 border-indigo-400 shadow shadow-indigo-500/40" : "bg-slate-900 border-slate-600"
                    }`} />
                    <div className="rounded-xl border border-white/[0.06] bg-slate-950/40 p-4 ml-2">
                      <div className="flex flex-col sm:flex-row sm:justify-between gap-2">
                        <div>
                          <h4 className="font-semibold text-sm text-slate-100">{exp.title}</h4>
                          <p className="text-xs text-indigo-300/90 mt-0.5">{exp.company}</p>
                        </div>
                        <div className="text-left sm:text-right shrink-0">
                          <span className="text-[10px] font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded">
                            {exp.start_date} — {exp.end_date || "Present"}
                          </span>
                          <p className="text-[10px] text-slate-600 mt-1">
                            {Math.floor(exp.duration_months / 12) > 0 && `${Math.floor(exp.duration_months / 12)}y `}
                            {exp.duration_months % 12 > 0 && `${exp.duration_months % 12}mo`}
                          </p>
                        </div>
                      </div>
                      {exp.description && (
                        <p className="text-xs text-slate-400 mt-3 leading-relaxed border-t border-white/[0.04] pt-3">
                          {exp.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === "skills" && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Full Skill Profile</h3>
            {candidate.skills.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">No skills listed.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {candidate.skills.map((skill, idx) => {
                  const isMatched = matched.some(
                    (m) => m.toLowerCase() === skill.name.toLowerCase()
                  );
                  return (
                    <div
                      key={idx}
                      className={`rounded-xl border p-3 ${
                        isMatched
                          ? "border-emerald-500/25 bg-emerald-500/[0.04]"
                          : "border-white/[0.06] bg-slate-950/30"
                      }`}
                    >
                      <div className="flex justify-between items-start gap-2">
                        <span className="font-medium text-sm text-slate-200">{skill.name}</span>
                        <span className="text-[9px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {skill.proficiency}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-2">
                        {skill.duration_months} mo · {skill.endorsements} endorsements
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {activeTab === "signals" && (
          <section className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Recruiter Signals</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  label: "Open to Work",
                  value: candidate.redrob_signals.open_to_work_flag ? "Yes" : "Passive",
                  highlight: candidate.redrob_signals.open_to_work_flag,
                },
                {
                  label: "Profile Completeness",
                  value: `${candidate.redrob_signals.profile_completeness_score}%`,
                  highlight: candidate.redrob_signals.profile_completeness_score >= 80,
                },
                {
                  label: "GitHub Activity",
                  value:
                    candidate.redrob_signals.github_activity_score >= 0
                      ? `${candidate.redrob_signals.github_activity_score}/100`
                      : "N/A",
                  highlight: candidate.redrob_signals.github_activity_score >= 60,
                },
                {
                  label: "Recruiter Response Rate",
                  value: `${Math.round(candidate.redrob_signals.recruiter_response_rate * 100)}%`,
                  highlight: candidate.redrob_signals.recruiter_response_rate >= 0.5,
                },
              ].map((signal) => (
                <div
                  key={signal.label}
                  className={`rounded-xl border p-4 ${
                    signal.highlight
                      ? "border-emerald-500/25 bg-emerald-500/[0.04]"
                      : "border-white/[0.06] bg-slate-950/30"
                  }`}
                >
                  <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">{signal.label}</div>
                  <div className={`text-sm font-semibold mt-1.5 ${signal.highlight ? "text-emerald-300" : "text-slate-300"}`}>
                    {signal.value}
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-white/[0.06] bg-slate-950/30 p-4">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-slate-400">Profile Completeness</span>
                <span className="text-slate-300 font-semibold">{candidate.redrob_signals.profile_completeness_score}%</span>
              </div>
              <div className="h-2 bg-slate-900 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full"
                  style={{ width: `${candidate.redrob_signals.profile_completeness_score}%` }}
                />
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
