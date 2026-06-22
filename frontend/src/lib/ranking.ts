export const RANKING_WEIGHTS = {
  semantic: 27,
  skills: 30,
  experience: 10,
  role: 28,
  activity: 5,
} as const;

export const RANKING_FORMULA =
  "Overall = 27% Semantic + 30% Skills + 10% Experience + 28% Role + 5% Activity";

export const RANKING_FORMULA_HELP =
  "Activity is gated by role and skill fit, so engagement signals cannot lift an unrelated profile above a better fit.";

export function scorePercent(score: number | null | undefined): number {
  if (score == null || Number.isNaN(score)) return 0;
  return Math.round(score * 100);
}

export function fitColorClass(percent: number): string {
  if (percent >= 75) return "text-emerald-400";
  if (percent >= 55) return "text-indigo-300";
  if (percent >= 35) return "text-amber-400";
  return "text-slate-500";
}

export function rankBadgeClass(rank: number): string {
  if (rank === 1) return "bg-gradient-to-br from-amber-300 to-yellow-500 text-slate-950 shadow-md shadow-amber-500/25";
  if (rank === 2) return "bg-gradient-to-br from-slate-100 to-slate-400 text-slate-950 shadow-md shadow-slate-400/15";
  if (rank === 3) return "bg-gradient-to-br from-orange-300 to-amber-700 text-white shadow-md shadow-orange-500/15";
  return "bg-slate-800/80 text-slate-400";
}

export function rankTone(rank: number): string {
  if (rank === 1) return "Gold";
  if (rank === 2) return "Silver";
  if (rank === 3) return "Bronze";
  return "Ranked";
}
