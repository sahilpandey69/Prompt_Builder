from typing import Any

from backend.config import get_settings

_FALLBACK: list[dict[str, Any]] = [
    {"id": "bfsi-loan-reminder", "name": "BFSI Loan Reminder", "description": "Template for loan payment reminders", "use_count": 0, "avg_rating": 0.0, "language": "English", "category": "BFSI"},
    {"id": "bfsi-appointment-booking", "name": "BFSI Appointment Booking", "description": "Template for booking branch or agent appointments", "use_count": 0, "avg_rating": 0.0, "language": "English", "category": "BFSI"},
]
_mongo_client = None


def _get_mongo():
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client
    uri = get_settings().mongo_uri
    if not uri:
        return None
    try:
        from pymongo import MongoClient
        _mongo_client = MongoClient(uri)
        _mongo_client.admin.command("ping")
        return _mongo_client
    except Exception:
        return None


def list_templates() -> list[dict[str, Any]]:
    client = _get_mongo()
    if client:
        try:
            db = client.get_database("prompt_builder")
            coll = db.get_collection("templates")
            cursor = coll.find({})
            return [{"id": d.get("id"), "name": d.get("name"), "description": d.get("description"), "use_count": d.get("use_count", 0), "avg_rating": d.get("avg_rating", 0.0), "language": d.get("language", "English"), "category": d.get("category", "BFSI"), "version": d.get("version", 1)} for d in cursor]
        except Exception:
            pass
    return _FALLBACK


def get_template(template_id: str) -> dict[str, Any] | None:
    for t in list_templates():
        if t.get("id") == template_id:
            return t
    return None
