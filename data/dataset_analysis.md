# Redrob AI Candidate Discovery Dataset Analysis

This report provides a detailed inspection, analysis, and statistical summary of the challenge candidate dataset.

---

## 1. Dataset Overview

*   **Total Records**: 100,000 candidate profiles
*   **Format**: JSON Lines (JSONL) format (`candidates.jsonl` uncompressed size ~487 MB)
*   **Target Variables**: None directly provided (unsupervised candidate ranking task against a target Job Description).
*   **Primary Keys**: `candidate_id` (Pattern: `^CAND_[0-9]{7}$`, e.g. `CAND_0000001` through `CAND_0100000`)
*   **Field Structure**:
    *   `candidate_id` (Unique string ID)
    *   `profile` (Biographical & professional header details)
    *   `career_history` (Historical employment record timeline list)
    *   `education` (Degree and academic institution record list)
    *   `skills` (Skill tag names, proficiencies, duration, and endorsement counts)
    *   `certifications` (Optional credentials list)
    *   `languages` (Languages and proficiency tiers list)
    *   `redrob_signals` (23 engagement and activity statistics)

---

## 2. Column and Field Descriptions

### Profile Fields
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `anonymized_name` | String | Candidate's name (anonymized) |
| `headline` | String | Professional headline summary |
| `summary` | String | Detailed career objective and professional highlights |
| `location` | String | Location (City, region/state) |
| `country` | String | Country of residence |
| `years_of_experience` | Float | Declared years of professional experience (Range: 1.0 to 16.9) |
| `current_title` | String | Current job title |
| `current_company` | String | Current employer |
| `current_company_size`| String | Size bucket of the employer (e.g. 1-10, 10001+) |
| `current_industry` | String | Current industry vertical |

### Career History Fields (List of Jobs)
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `company` | String | Name of the employer company |
| `title` | String | Role title |
| `start_date` | Date | Start date of the role (YYYY-MM-DD) |
| `end_date` | Date/Null | End date of the role (null if `is_current` is true) |
| `duration_months` | Integer | Total duration of the role in months |
| `is_current` | Boolean | Whether this is the active current job |
| `industry` | String | Company industry |
| `company_size` | String | Employer company size |
| `description` | String | Detailed description of tasks, achievements, and technology |

### Education Fields (List of Degrees)
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `institution` | String | University or school name |
| `degree` | String | Degree type (e.g. B.Tech, M.S., Ph.D.) |
| `field_of_study` | String | Field of study (e.g. Machine Learning, CS) |
| `start_year` | Integer | Starting year of study |
| `end_year` | Integer | Graduation year |
| `grade` | String/Null| GPA or score details |
| `tier` | String | Internal prestige tier (tier_1 to tier_4, unknown) |

### Skills Fields (List of Skills)
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `name` | String | Standard skill tag name |
| `proficiency` | String | Proficiency level (beginner, intermediate, advanced, expert) |
| `endorsements` | Integer | Total endorsements received on platform |
| `duration_months` | Integer | Total months of usage of this skill |

### Platform Signals Fields (redrob_signals)
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `profile_completeness_score`| Float | Percentage profile completion (0 to 100) |
| `signup_date` | Date | Signup date on the platform |
| `last_active_date` | Date | Last date candidate logged in |
| `open_to_work_flag` | Boolean | Actively looking for a job flag |
| `recruiter_response_rate` | Float | Rate at which recruiters get replies (0 to 1) |
| `notice_period_days` | Integer | Required notice period in days (0 to 180) |
| `expected_salary_range_inr_lpa`| Object | min/max expected salary in INR LPA |
| `github_activity_score` | Float | Score based on GitHub PRs/commits (-1 if not linked) |
| `willing_to_relocate` | Boolean | Relocation availability |
| `preferred_work_mode` | String | remote, hybrid, onsite, flexible |

---

## 3. Data Quality Issues & Anomalies

Through dynamic inspection of the candidate pool, several critical inconsistencies were identified:

1.  **Honeypot/Date Logic Violations (255 candidates)**:
    *   Candidates claim to have worked at specific startups *before* the startup was founded.
    *   *Examples*: Worked at **CRED** (founded 2018) starting in 2017, or **Krutrim** (founded 2023) starting in 2019/2022, or **Sarvam AI** (founded 2023) starting in 2020.
    *   These constitute the "honeypots" referenced in the hackathon rules and are forced to relevance tier 0. If ranked in the top 100, they cause disqualification.
2.  **Temporal Profile Inconsistencies (7,496 candidates)**:
    *   `last_active_date` is earlier than `signup_date` in 7.5% of records.
    *   Career start date is significantly before education start year (812 candidates). E.g., working 10 years before entering university.
3.  **Salary Expectation Anomalies (18,865 candidates)**:
    *   Expected salary minimum is greater than maximum (18.8% of records).
4.  **Skills Anomalies (21 candidates)**:
    *   Candidates claiming to have "expert" or "advanced" proficiency in skills with `duration_months` equal to 0.

---

## 4. Recommended Preprocessing & Filtering Steps

To ensure high-quality, robust candidate matching and avoid disqualifications, we implement the following ingestion pipelines:

1.  **Strict Honeypot Filter**:
    *   Perform a look-up scan against startup founding dates during candidate retrieval.
    *   Discard candidates showing temporal start violations at Krutrim, Sarvam AI, CRED, Glance, or Rephrase.ai.
2.  **Text Clean and Normalization**:
    *   Trim extra whitespaces, normalize special characters, and lowercase strings for search matching.
3.  **Skill Synonym Mapping**:
    *   Map skill names (e.g. "react.js", "reactjs", "react" -> "React"; "ml", "machine learning" -> "Machine Learning") to ensure uniform matching representation.
4.  **Behavioral Weight Modifiers**:
    *   Do not rank candidates with extremely low response rates (< 15%) or who have been completely inactive for over 180 days, as they are likely unreachable or inactive talent.

---

## 5. Candidate Discovery Opportunities

*   **Hybrid Semantic Retrieval**: Combine dense text embeddings of professional summaries/headlines with keyword index match lists.
*   **Role-to-Title Alignment**: Filter out keyword-stuffed resumes (e.g. "Marketing Manager" claiming to be a "RAG expert") by checking the consistency of their active job titles in `career_history`.
*   **Reachability Score multiplier**: Use `recruiter_response_rate` and `notice_period_days` to score candidates who are highly active and immediately available.
