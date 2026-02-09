import os
from typing import Any

import httpx

# Backend URL; frontend and backend often run on different ports
BASE_URL = os.environ.get("PROMPT_BUILDER_API_URL", "http://localhost:8000")


def _headers() -> dict[str, str]:
    token = os.environ.get("SIMPLE_PASSWORD", "")
    return {"X-Auth-Token": token, "Content-Type": "application/json"}


def create_prompt(session_id: str | None, input_type: str, content: Any) -> dict[str, Any]:
    payload = {
        "session_id": session_id,
        "input": {
            "type": input_type,
            "content": content,
        },
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{BASE_URL}/api/v1/prompt/create",
            json=payload,
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


def answer_questions(session_id: str, answers: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{BASE_URL}/api/v1/prompt/answer",
            json={"session_id": session_id, "answers": answers},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


def get_result(session_id: str) -> dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{BASE_URL}/api/v1/prompt/{session_id}/result",
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


def get_history() -> list[dict[str, Any]]:
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE_URL}/api/v1/prompt/history", headers=_headers())
        r.raise_for_status()
        data = r.json()
        return data.get("sessions", [])


def submit_feedback(session_id: str, deployed: bool, rating: int, issues: str = "") -> None:
    with httpx.Client(timeout=10.0) as client:
        client.post(
            f"{BASE_URL}/api/v1/prompt/{session_id}/feedback",
            json={"deployed": deployed, "rating": rating, "issues": issues},
            headers=_headers(),
        )


def list_templates() -> list[dict[str, Any]]:
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE_URL}/api/v1/templates", headers=_headers())
        r.raise_for_status()
        data = r.json()
        return data.get("templates", [])
