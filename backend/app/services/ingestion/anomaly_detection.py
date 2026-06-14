import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

# Default path to company founding dates JSON configuration
DEFAULT_FOUNDING_DATES_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../data/company_founding_dates.json"
    )
)

def _to_dict(obj: Any) -> Dict[str, Any]:
    """Helper to convert Pydantic model or dict to dictionary representation."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj

def parse_year(date_str: Optional[str]) -> Optional[int]:
    """Extracts year as integer from a date string (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        return int(date_str.split("-")[0])
    except Exception:
        return None

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parses date string (YYYY-MM-DD) to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def detect_temporal_anomalies(candidate: Union[Dict[str, Any], Any], founding_dates: Optional[Dict[str, int]] = None) -> List[str]:
    """
    Checks for temporal anomalies in a candidate profile:
    1. Joined a startup before its founding year (startup_join_date < startup_founding_date).
    2. Career start date is before education start date (with a buffer).
    3. Last active date is before the signup date.
    4. Start date is after end date in any career history entry.
    
    Returns:
        List of anomaly description strings.
    """
    data = _to_dict(candidate)
    anomalies = []
    
    # Load default founding dates if not provided
    if founding_dates is None:
        if os.path.exists(DEFAULT_FOUNDING_DATES_PATH):
            try:
                with open(DEFAULT_FOUNDING_DATES_PATH, "r", encoding="utf-8") as f:
                    founding_dates = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load founding dates: {e}")
                founding_dates = {}
        else:
            founding_dates = {}
            
    career_history = data.get("career_history", [])
    education = data.get("education", [])
    signals = data.get("redrob_signals", {})
    profile = data.get("profile", {})
    
    # Check 1 & 4: Startup join date < founding date and Start date > End date
    career_years = []
    for job in career_history:
        company = job.get("company", "")
        start_date_str = job.get("start_date")
        end_date_str = job.get("end_date")
        
        start_year = parse_year(start_date_str)
        career_years.append(start_year)
        
        # Check startup founding violation
        if company in founding_dates and start_year:
            found_year = founding_dates[company]
            if start_year < found_year:
                anomalies.append(
                    f"Temporal anomaly: worked at '{company}' starting in {start_date_str} but company was founded in {found_year}."
                )
                
        # Check start date > end date
        if start_date_str and end_date_str:
            start_dt = parse_date(start_date_str)
            end_dt = parse_date(end_date_str)
            if start_dt and end_dt and start_dt > end_dt:
                anomalies.append(
                    f"Temporal anomaly: job at '{company}' has start date {start_date_str} after end date {end_date_str}."
                )
                
    # Check 2: Career start before education start
    edu_years = [edu.get("start_year") for edu in education if edu.get("start_year")]
    if edu_years and career_years:
        earliest_edu = min(edu_years)
        # Filter None values from career years
        valid_career_years = [y for y in career_years if y is not None]
        if valid_career_years:
            earliest_career = min(valid_career_years)
            # 4 years buffer for working during university / high school
            if earliest_career < earliest_edu - 4:
                anomalies.append(
                    f"Temporal anomaly: career started in {earliest_career} which is significantly before education start year {earliest_edu}."
                )
                
    # Check 3: Last active before signup
    signup_str = signals.get("signup_date")
    last_active_str = signals.get("last_active_date")
    if signup_str and last_active_str:
        signup_dt = parse_date(signup_str)
        last_active_dt = parse_date(last_active_str)
        if signup_dt and last_active_dt and last_active_dt < signup_dt:
            anomalies.append(
                f"Temporal anomaly: last active date {last_active_str} is before signup date {signup_str}."
            )
            
    return anomalies

def detect_profile_inconsistencies(candidate: Union[Dict[str, Any], Any]) -> List[str]:
    """
    Checks for semantic profile inconsistencies:
    1. Declared total years of experience is significantly less than individual job duration.
    2. Skills with advanced/expert proficiency but 0 duration.
    3. Salary expectations min > max.
    
    Returns:
        List of inconsistency description strings.
    """
    data = _to_dict(candidate)
    inconsistencies = []
    
    profile = data.get("profile", {})
    career_history = data.get("career_history", [])
    skills = data.get("skills", [])
    signals = data.get("redrob_signals", {})
    
    # Check 1: Experience duration vs declared total experience
    declared_exp = profile.get("years_of_experience", 0.0)
    for job in career_history:
        duration_months = job.get("duration_months", 0)
        job_years = duration_months / 12.0
        if job_years > declared_exp + 1.0: # 1 year grace margin for estimation roundings
            inconsistencies.append(
                f"Profile inconsistency: candidate has job at '{job.get('company')}' for {job_years:.1f} years, exceeding total profile experience of {declared_exp} years."
            )
            break # Flag once
            
    # Check 2: Expert/Advanced skills with 0 duration
    expert_zero_dur = []
    for skill in skills:
        name = skill.get("name", "")
        proficiency = skill.get("proficiency", "").lower()
        duration = skill.get("duration_months", 0)
        if proficiency in ["expert", "advanced"] and duration == 0:
            expert_zero_dur.append(name)
            
    if len(expert_zero_dur) >= 3: # Flag if 3 or more skills have this anomaly
        inconsistencies.append(
            f"Profile inconsistency: candidate has expert/advanced proficiency but 0 duration in {len(expert_zero_dur)} skills: {', '.join(expert_zero_dur[:5])}."
        )
        
    # Check 3: Expected salary min > max
    salary = signals.get("expected_salary_range_inr_lpa", {})
    min_sal = salary.get("min")
    max_sal = salary.get("max")
    if min_sal is not None and max_sal is not None and min_sal > max_sal:
        inconsistencies.append(
            f"Profile inconsistency: expected salary minimum {min_sal} LPA is greater than maximum {max_sal} LPA."
        )
        
    return inconsistencies

def generate_anomaly_report(candidates: List[Union[Dict[str, Any], Any]], founding_dates: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Analyzes a collection of candidate profiles and generates a detailed anomaly report.
    """
    total_analyzed = 0
    temporal_anomalies_count = 0
    profile_inconsistencies_count = 0
    both_anomalies_count = 0
    clean_count = 0
    
    anomaly_categories = {
        "startup_founding_violation": 0,
        "job_start_after_end": 0,
        "career_starts_before_education": 0,
        "active_before_signup": 0,
        "experience_duration_exceeds_total": 0,
        "expert_skills_zero_duration": 0,
        "salary_min_gt_max": 0
    }
    
    flagged_candidates = []
    
    for cand in candidates:
        total_analyzed += 1
        data = _to_dict(cand)
        cid = data.get("candidate_id", "UNKNOWN")
        
        temp_anoms = detect_temporal_anomalies(data, founding_dates)
        prof_incons = detect_profile_inconsistencies(data)
        
        # Categorize
        has_temp = len(temp_anoms) > 0
        has_incons = len(prof_incons) > 0
        
        if has_temp:
            temporal_anomalies_count += 1
        if has_incons:
            profile_inconsistencies_count += 1
        if has_temp and has_incons:
            both_anomalies_count += 1
        if not has_temp and not has_incons:
            clean_count += 1
            
        # Detail categories
        for anom in temp_anoms:
            if "founded" in anom:
                anomaly_categories["startup_founding_violation"] += 1
            elif "after end date" in anom:
                anomaly_categories["job_start_after_end"] += 1
            elif "before education" in anom:
                anomaly_categories["career_starts_before_education"] += 1
            elif "before signup" in anom:
                anomaly_categories["active_before_signup"] += 1
                
        for incons in prof_incons:
            if "exceeding total profile experience" in incons:
                anomaly_categories["experience_duration_exceeds_total"] += 1
            elif "expert/advanced proficiency but 0 duration" in incons:
                anomaly_categories["expert_skills_zero_duration"] += 1
            elif "salary minimum" in incons:
                anomaly_categories["salary_min_gt_max"] += 1
                
        if has_temp or has_incons:
            flagged_candidates.append({
                "candidate_id": cid,
                "temporal_anomalies": temp_anoms,
                "profile_inconsistencies": prof_incons
            })
            
    return {
        "summary": {
            "total_analyzed": total_analyzed,
            "clean_profiles": clean_count,
            "flagged_profiles": len(flagged_candidates),
            "temporal_anomalies": temporal_anomalies_count,
            "profile_inconsistencies": profile_inconsistencies_count,
            "both_types": both_anomalies_count
        },
        "categories": anomaly_categories,
        "sample_flagged": flagged_candidates[:20]
    }
