from typing import Dict, Any, List, Optional, Tuple


class ExplainabilityService:
    """
    Generates structured recruiter-friendly explanations for candidate ranking.

    Skill lists always come from ranking pre-compute (_matched_skills / _missed_skills)
    so matched, missing, and skill % share a single source of truth.
    """

    def __init__(self) -> None:
        pass

    def _resolve_skills(
        self, required_skills: List[str], candidate: Dict[str, Any]
    ) -> Tuple[List[str], List[str], int]:
        """Return (matched, missing, skill_match_percent) from ranking artifacts."""
        matched = list(candidate.get("_matched_skills") or [])
        missing = list(candidate.get("_missed_skills") or [])
        skill_pct = candidate.get("_skill_match_percent")
        if skill_pct is None and required_skills:
            skill_pct = int(len(matched) / len(required_skills) * 100)
        elif skill_pct is None:
            skill_pct = 0
        return matched, missing, int(skill_pct)

    def generate_ranking_reasons(
        self,
        job_title: str,
        required_skills: List[str],
        candidate: Dict[str, Any],
        semantic_similarity: Optional[float] = None,
        rank: int = 0,
    ) -> List[str]:
        """Recruiter-friendly bullet reasons ordered by ranking importance."""
        profile = candidate.get("profile", {})
        cand_exp = float(profile.get("years_of_experience", 0.0))
        cand_title = profile.get("current_title", "") or profile.get("headline", "")

        matched, missing, skill_pct = self._resolve_skills(required_skills, candidate)
        title_align = float(candidate.get("_title_alignment", 0.0))
        title_pct = int(title_align * 100)
        sem_pct = int((semantic_similarity or 0.0) * 100)

        signals = candidate.get("redrob_signals", {})
        reasons: List[str] = []

        # 1. Title / role alignment (highest priority)
        job_norm = job_title.strip().lower()
        cand_norm = cand_title.strip().lower()
        if job_norm and cand_norm and job_norm == cand_norm:
            reasons.append(f"Exact {job_title} title match")
        elif title_pct >= 85:
            reasons.append(f"Strong title alignment — {cand_title} ({title_pct}% role fit)")
        elif title_pct >= 65:
            reasons.append(f"High role alignment — {cand_title} ({title_pct}% role fit)")
        elif title_pct >= 40:
            reasons.append(f"Partial role alignment with {job_title} ({title_pct}%)")
        elif title_pct > 0:
            reasons.append(f"Limited role alignment — current title: {cand_title}")

        # 2. Required skills
        req_count = len(required_skills)
        if req_count > 0:
            if matched:
                for skill in matched[:4]:
                    reasons.append(f"{skill} matched")
                reasons.append(f"{len(matched)}/{req_count} required skills matched ({skill_pct}% skill fit)")
            else:
                reasons.append("No required skills matched in profile")

        # 3. Semantic alignment
        if semantic_similarity is not None and semantic_similarity > 0:
            if sem_pct >= 75:
                reasons.append(f"Strong semantic alignment ({sem_pct}%)")
            elif sem_pct >= 50:
                reasons.append(f"Good semantic alignment ({sem_pct}%)")
            else:
                reasons.append(f"Moderate semantic alignment ({sem_pct}%)")

        # 4. Experience
        if cand_exp > 0:
            exp_score = float(candidate.get("_experience_match", 0.0))
            if exp_score >= 0.6:
                reasons.append(f"{cand_exp:.0f} years relevant experience")
            else:
                reasons.append(f"{cand_exp:.0f} years experience in field")

        # 5. Profile strength (only when fit is already reasonable)
        fit_gate = float(candidate.get("_activity_fit_gate", 0.0))
        if fit_gate >= 0.4:
            if signals.get("open_to_work_flag"):
                reasons.append("Active job seeker")
            github = float(signals.get("github_activity_score", -1.0))
            if github >= 60:
                reasons.append(f"Active GitHub profile ({int(github)}/100)")

        if rank == 1 and not reasons:
            reasons.append("Top-ranked by hybrid role + skill + semantic scoring")

        return reasons

    def generate_explanation(
        self,
        job_title: str,
        required_skills: List[str],
        candidate: Dict[str, Any],
        semantic_similarity: Optional[float] = None,
        rank: int = 0,
    ) -> str:
        """
        Creates a structured explanation with matched/missing skills and bulleted reasons.
        """
        matched, missing, _ = self._resolve_skills(required_skills, candidate)
        reasons = self.generate_ranking_reasons(
            job_title, required_skills, candidate, semantic_similarity, rank
        )

        title = f"Why Ranked #{rank}" if rank else "Why Ranked"
        positive_lines = [f"+ {reason}" for reason in reasons]
        if not positive_lines:
            positive_lines.append("+ Ranked by deterministic role, skill, semantic, experience, and activity signals")

        missing_lines = [f"- {skill}" for skill in missing]
        if not missing_lines:
            missing_lines.append("- No required skills missing")

        matched_str = ", ".join(matched) if matched else "None"
        return (
            f"{title}\n\n"
            + "\n".join(positive_lines)
            + f"\n\nMatched Skills: {matched_str}\n\n"
            + "Missing:\n"
            + "\n".join(missing_lines)
        )
