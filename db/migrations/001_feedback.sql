-- Feedback table for prompt builder (Phase 2 when Postgres is connected)
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    deployed BOOLEAN DEFAULT FALSE,
    rating INTEGER DEFAULT 0,
    issues TEXT,
    manual_edits TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
