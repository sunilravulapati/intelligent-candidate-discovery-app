# Dataset Verification Report

This report verifies the metadata, schema structures, and contents of the challenge candidate pool.

---

## 1. Candidate Dataset Profile

*   **File Name**: `candidates.jsonl`
*   **Location**: `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl`
*   **Total Record Count**: 100,000 candidates
*   **File Format**: JSON Lines (JSONL), UTF-8 encoded
*   **File Size**: 487,259,903 bytes (approx. 465 MB)

---

## 2. Structural Schemas & Columns

The schema matches the definitions inside `candidate_schema.json`:

### Bio & Header Fields (`profile`)
- `anonymized_name` (String)
- `headline` (String)
- `summary` (String)
- `location` (String)
- `country` (String)
- `years_of_experience` (Float)
- `current_title` (String)
- `current_company` (String)
- `current_company_size` (String, enum: 1-10 to 10001+)
- `current_industry` (String)

### Skills Fields (`skills` - Array of Skill Objects)
- `name` (String, normalized skill tag name)
- `proficiency` (String, enum: beginner, intermediate, advanced, expert)
- `endorsements` (Integer >= 0)
- `duration_months` (Integer >= 0, total months of usage)

### Career Experience Fields (`career_history` - Array of Job Objects)
- `company` (String)
- `title` (String)
- `start_date` (Date string)
- `end_date` (Date string / null)
- `duration_months` (Integer)
- `is_current` (Boolean)
- `industry` (String)
- `company_size` (String)
- `description` (String)

### Education Fields (`education` - Array of Academic Objects)
- `institution` (String)
- `degree` (String)
- `field_of_study` (String)
- `start_year` (Integer)
- `end_year` (Integer)
- `grade` (String / null)
- `tier` (String, enum: tier_1 to tier_4, unknown)

### Activity Signals (`redrob_signals` - Object of Platform Activity Indicators)
- Contains 23 activity metrics:
  - `profile_completeness_score` (Float)
  - `signup_date` (Date)
  - `last_active_date` (Date)
  - `open_to_work_flag` (Boolean)
  - `profile_views_received_30d` (Integer)
  - `applications_submitted_30d` (Integer)
  - `recruiter_response_rate` (Float)
  - `avg_response_time_hours` (Float)
  - `skill_assessment_scores` (Dict[String, Float])
  - `connection_count` (Integer)
  - `endorsements_received` (Integer)
  - `notice_period_days` (Integer)
  - `expected_salary_range_inr_lpa` (ExpectedSalaryRange)
  - `preferred_work_mode` (String)
  - `willing_to_relocate` (Boolean)
  - `github_activity_score` (Float)
  - `search_appearance_30d` (Integer)
  - `saved_by_recruiters_30d` (Integer)
  - `interview_completion_rate` (Float)
  - `offer_acceptance_rate` (Float)
  - `verified_email` (Boolean)
  - `verified_phone` (Boolean)
  - `linkedin_connected` (Boolean)

---

## 3. Target Variables & Labels
*   No training labels or target ranking outcomes exist in the dataset.
*   The matching and ranking task is unsupervised. The objective is to retrieve and sort candidates dynamically according to Jaccard skill overlaps, title matching, and behavioral indicators.
