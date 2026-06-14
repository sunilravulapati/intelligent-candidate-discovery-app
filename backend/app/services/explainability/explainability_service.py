from typing import Dict, Any, List, Optional


class ExplainabilityService:
    """
    Generates structured AI insights explaining why a candidate matches a specific job role.

    Output format:
        Matched:
        <comma-separated matched skills>

        Missing:
        <comma-separated missing skills>

        Reason:
        <recruiter-friendly narrative>
    """

    def __init__(self) -> None:
        pass

    def generate_explanation(
        self,
        job_title: str,
        required_skills: List[str],
        candidate: Dict[str, Any],
        semantic_similarity: Optional[float] = None,
    ) -> str:
        """
        Creates a structured explanation showing matched/missing skills and a
        recruiter-friendly reason that includes semantic alignment when available.

        Args:
            job_title: The target job title.
            required_skills: List of required skills from the job query.
            candidate: Candidate profile dict (as returned by ingestion service).
            semantic_similarity: Cosine similarity score [0, 1] from FAISS, or None in
                                 keyword-fallback mode.

        Returns:
            str: Multi-section explanation string.
        """
        profile = candidate.get("profile", {})
        cand_exp = float(profile.get("years_of_experience", 0.0))
        cand_title = profile.get("current_title", "")

        # ── Skill intersection ─────────────────────────────────────────
        req_lower = [s.lower() for s in required_skills]
        cand_skills_raw = candidate.get("skills", [])
        cand_skill_names = [s.get("name", "") for s in cand_skills_raw]
        cand_skills_lower = [s.lower() for s in cand_skill_names]

        matched_skills: List[str] = []
        missing_skills: List[str] = []

        for req in required_skills:
            if req.lower() in cand_skills_lower:
                # Preserve original casing from candidate profile
                idx = cand_skills_lower.index(req.lower())
                matched_skills.append(cand_skill_names[idx])
            else:
                missing_skills.append(req)

        # ── Reason narrative ───────────────────────────────────────────
        signals = candidate.get("redrob_signals", {})
        open_to_work = signals.get("open_to_work_flag", False)
        github_score = float(signals.get("github_activity_score", -1.0))

        reasons: List[str] = []

        # Semantic alignment (first, most important)
        if semantic_similarity is not None and semantic_similarity > 0:
            sem_pct = int(semantic_similarity * 100)
            if sem_pct >= 75:
                strength = "Strong"
            elif sem_pct >= 50:
                strength = "Good"
            else:
                strength = "Moderate"
            reasons.append(
                f"{strength} semantic alignment with {job_title} requirements "
                f"({sem_pct}% semantic match)."
            )

        # Experience
        if cand_exp > 0:
            reasons.append(
                f"{cand_exp} years of professional experience as a {cand_title}."
                if cand_title
                else f"{cand_exp} years of professional experience."
            )

        # Skill overlap
        if matched_skills:
            overlap_pct = int(len(matched_skills) / max(len(required_skills), 1) * 100)
            reasons.append(f"{overlap_pct}% required skill overlap.")
        else:
            reasons.append("No direct match with required skills found in profile.")

        # Activity signals
        if open_to_work:
            reasons.append("Candidate is actively open to new roles.")
        if github_score >= 60:
            reasons.append(
                f"Strong open-source engagement (GitHub score: {int(github_score)}/100)."
            )

        # ── Format output ──────────────────────────────────────────────
        matched_str = ", ".join(matched_skills) if matched_skills else "None"
        missing_str = ", ".join(missing_skills) if missing_skills else "None"
        reason_str = " ".join(reasons)

        return (
            f"Matched:\n{matched_str}\n\n"
            f"Missing:\n{missing_str}\n\n"
            f"Reason:\n{reason_str}"
        )
