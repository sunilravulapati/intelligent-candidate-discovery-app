-- DDL Schema for Optional PostgreSQL DB Setup

-- Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(50) PRIMARY KEY, -- Format: CAND_XXXXXXX
    name VARCHAR(255) NOT NULL,
    headline VARCHAR(500),
    summary TEXT,
    location VARCHAR(255),
    country VARCHAR(100),
    years_of_experience NUMERIC(4, 2),
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    skills JSONB, -- Nested skills array
    career_history JSONB, -- Nested history array
    education JSONB, -- Nested education array
    redrob_signals JSONB, -- Redrob engagement metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    required_skills JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Search Query Logs (Recruiter queries)
CREATE TABLE IF NOT EXISTS search_queries (
    id SERIAL PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    results_count INTEGER,
    retrieval_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
