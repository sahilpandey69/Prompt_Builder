import json
from typing import Any

from backend.config import get_settings

_sessions: dict[str, dict[str, Any]] = {}
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    url = get_settings().redis_url
    if not url:
        return None
    try:
        import redis
        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None


def _serialize(state: dict[str, Any]) -> str:
    return json.dumps(state, default=str)


def _deserialize(s: str) -> dict[str, Any] | None:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def get_session(session_id: str) -> dict[str, Any] | None:
    r = _get_redis()
    if r:
        try:
            data = r.get(f"prompt_builder:session:{session_id}")
            return _deserialize(data) if data else None
        except Exception:
            pass
    return _sessions.get(session_id)


def set_session(session_id: str, state: dict[str, Any]) -> None:
    r = _get_redis()
    if r:
        try:
            r.setex(
                f"prompt_builder:session:{session_id}",
                86400 * 7,  # 7 days
                _serialize(state),
            )
            return
        except Exception:
            pass
    _sessions[session_id] = state


def merge_session(session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    current = get_session(session_id) or {}
    merged = {**current, **updates}
    set_session(session_id, merged)
    return merged


def list_session_ids() -> list[str]:
    """List session IDs that have completed prompts (for History)."""
    r = _get_redis()
    if r:
        try:
            keys = r.keys("prompt_builder:session:*")
            return [k.replace("prompt_builder:session:", "") for k in keys]
        except Exception:
            pass
    return list(_sessions.keys())
