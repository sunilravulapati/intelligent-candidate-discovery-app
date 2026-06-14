import pandas as pd
from typing import Dict, Any, List


class XGBoostFeatureEngineer:
    """
    Handles feature engineering for tabular models (XGBoost/LightGBM)
    comparing job requirements against retrieved candidates.
    """

    def __init__(self) -> None:
        pass

    def extract_features(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, float]:
        """
        Extracts numerical and categorical features for a single candidate-job pair.
        
        Args:
            job: Dictionary containing job details (title, description, required_skills, etc.).
            candidate: Dictionary containing candidate profile schema.
            
        Returns:
            Dict[str, float]: Flat feature dictionary.
        """
        features = {}

        # 1. Experience features
        cand_profile = candidate.get("profile", {})
        cand_exp = float(cand_profile.get("years_of_experience", 0.0))
        features["years_of_experience"] = cand_exp
        
        # 2. Skill overlap features
        job_skills = set(job.get("required_skills", []))
        cand_skills = {s.get("name", "").lower() for s in candidate.get("skills", [])}
        overlap = len(job_skills.intersection(cand_skills))
        features["skill_overlap_count"] = float(overlap)
        features["skill_overlap_ratio"] = float(overlap) / max(len(job_skills), 1)

        # 3. Redrob engagement signal features
        signals = candidate.get("redrob_signals", {})
        features["profile_completeness_score"] = float(signals.get("profile_completeness_score", 0.0))
        features["open_to_work_flag"] = 1.0 if signals.get("open_to_work_flag", False) else 0.0
        features["github_activity_score"] = float(signals.get("github_activity_score", 0.0))
        features["notice_period_days"] = float(signals.get("notice_period_days", 0.0))
        features["recruiter_response_rate"] = float(signals.get("recruiter_response_rate", 0.0))
        features["connection_count"] = float(signals.get("connection_count", 0.0))

        # 4. Salary & Work mode match (dummy encoding or matching check)
        # Expected salary: signals.get("expected_salary_range_inr_lpa", {})
        # Preferred work mode: signals.get("preferred_work_mode", "")
        # Willing to relocate: signals.get("willing_to_relocate", False)
        
        return features

    def batch_extract_features(
        self, job: Dict[str, Any], candidates: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Extracts features for a batch of candidates for a single job.
        
        Args:
            job: Job description details.
            candidates: List of candidate profiles.
            
        Returns:
            pd.DataFrame: Feature matrix where each row represents a candidate-job pair.
        """
        all_features = []
        for cand in candidates:
            features = self.extract_features(job, cand)
            # Add candidate_id to link back
            features["candidate_id"] = cand.get("candidate_id", "")
            all_features.append(features)

        df = pd.DataFrame(all_features)
        if not df.empty:
            df.set_index("candidate_id", inplace=True)
        return df
