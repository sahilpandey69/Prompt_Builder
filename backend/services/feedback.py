from typing import Any

from backend.config import get_settings

_pg_pool = None


def _get_pg():
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool
    dsn = get_settings().postgres_dsn
    if not dsn:
        return None
    try:
        import psycopg2
        _pg_pool = psycopg2.connect(dsn)
        return _pg_pool
    except Exception:
        return None


def save_feedback(session_id: str, deployed: bool, rating: int, issues: str = "", manual_edits: str = "") -> None:
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    deployed BOOLEAN DEFAULT FALSE,
                    rating INTEGER DEFAULT 0,
                    issues TEXT,
                    manual_edits TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                "INSERT INTO feedback (session_id, deployed, rating, issues, manual_edits) VALUES (%s, %s, %s, %s, %s)",
                (session_id, deployed, rating, issues or None, manual_edits or None),
            )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        pass


def get_feedback_summary() -> dict[str, Any]:
    out = {"deployed_count": 0, "avg_rating": 0.0, "total_count": 0}
    conn = _get_pg()
    if not conn:
        return out
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), AVG(rating) FROM feedback WHERE deployed = TRUE")
            row = cur.fetchone()
            out["deployed_count"] = row[0] or 0
            out["avg_rating"] = round(float(row[1] or 0), 2)
            cur.execute("SELECT COUNT(*) FROM feedback")
            out["total_count"] = cur.fetchone()[0] or 0
    except Exception:
        pass
    return out
