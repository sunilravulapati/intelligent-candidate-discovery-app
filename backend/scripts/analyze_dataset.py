import os
import sys
import numpy as np
from collections import Counter

# Set up path so app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion.ingestion_service import IngestionService
from app.services.ingestion.anomaly_detection import generate_anomaly_report

def main():
    print("Initializing Ingestion Service...")
    service = IngestionService()
    
    status = service.get_candidate_files_status()
    print(f"Active dataset source: {status.get('active_source')}")
    print(f"File path: {status[status['active_source']]['path']}")
    
    print("Streaming and parsing candidates (processing up to 20,000 for quick stats)...")
    # Stream up to 20000 records for stats representation to keep it fast, or load all
    candidates = service.load_all_candidates(limit=20000, validate=True, preprocess=True, as_dict=False)
    total_loaded = len(candidates)
    print(f"Loaded and validated {total_loaded} candidate profiles.")
    
    if not candidates:
        print("No candidates loaded.")
        return
        
    # 1. Experience distribution
    exp_years = [c.profile.years_of_experience for c in candidates]
    mean_exp = np.mean(exp_years)
    median_exp = np.median(exp_years)
    min_exp = np.min(exp_years)
    max_exp = np.max(exp_years)
    
    print("\n=== Professional Experience ===")
    print(f"Years of Experience:")
    print(f"  Min:    {min_exp:.2f} yrs")
    print(f"  Max:    {max_exp:.2f} yrs")
    print(f"  Mean:   {mean_exp:.2f} yrs")
    print(f"  Median: {median_exp:.2f} yrs")
    
    # 2. Skill frequency analysis
    skills_counter = Counter()
    for c in candidates:
        for s in c.skills:
            skills_counter[s.name] += 1
            
    print("\n=== Top 20 Most Frequent Skills ===")
    for skill, freq in skills_counter.most_common(20):
        print(f"  {skill}: {freq} occurrences ({freq/total_loaded*100:.1f}%)")
        
    # 3. Activity signals distributions
    completeness = [c.redrob_signals.profile_completeness_score for c in candidates]
    response_rates = [c.redrob_signals.recruiter_response_rate for c in candidates]
    github_scores = [c.redrob_signals.github_activity_score for c in candidates if c.redrob_signals.github_activity_score != -1]
    connections = [c.redrob_signals.connection_count for c in candidates]
    open_to_work = sum(1 for c in candidates if c.redrob_signals.open_to_work_flag)
    
    print("\n=== Behavioral/Activity Signals ===")
    print(f"Profile Completeness: Mean={np.mean(completeness):.1f}%, Median={np.median(completeness):.1f}%")
    print(f"Recruiter Response Rate: Mean={np.mean(response_rates):.2f}, Median={np.median(response_rates):.2f}")
    if github_scores:
        print(f"GitHub Activity Score (excluding unlinked): Mean={np.mean(github_scores):.1f}, Median={np.median(github_scores):.1f}")
    else:
        print("GitHub Activity Score: None linked in this sample")
    print(f"Connection Count: Mean={np.mean(connections):.1f}, Median={np.median(connections):.1f}")
    print(f"Open to Work count: {open_to_work} ({open_to_work/total_loaded*100:.1f}%)")
    
    # 4. Generate anomaly report
    print("\n=== Dynamic Anomaly & Honeypot Check ===")
    report = generate_anomaly_report(candidates)
    print(f"Total Profiles Flagged: {report['summary']['flagged_profiles']} ({report['summary']['flagged_profiles']/total_loaded*100:.2f}%)")
    print(f"  - Startup Founding Violations (Honeypots): {report['categories']['startup_founding_violation']}")
    print(f"  - Active before Signup Violations: {report['categories']['active_before_signup']}")
    print(f"  - Career starts before Edu: {report['categories']['career_starts_before_education']}")
    print(f"  - Experience duration exceeds total profile: {report['categories']['experience_duration_exceeds_total']}")
    print(f"  - Expert skills with 0 duration: {report['categories']['expert_skills_zero_duration']}")
    print(f"  - Expected Salary min > max: {report['categories']['salary_min_gt_max']}")

if __name__ == "__main__":
    main()
