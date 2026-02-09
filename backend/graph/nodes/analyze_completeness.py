import json
from typing import Any

from backend.graph.state import PromptBuilderState
from backend.llm import call_llm
from backend.llm.prompts import REASONING_SYSTEM_PROMPT


def analyze_completeness_node(state: PromptBuilderState) -> dict[str, Any]:
    extracted = state.get("extracted_data") or {}
    raw = state.get("raw_input") or ""
    user_content = f"Parsed data:\n{json.dumps(extracted, indent=2)}\n\nRaw input excerpt:\n{raw[:2000]}"
    try:
        out = call_llm(REASONING_SYSTEM_PROMPT, user_content)
        if out.startswith("```"):
            out = out.split("```", 2)[1]
            if out.startswith("json"):
                out = out[4:]
        data = json.loads(out.strip())
    except Exception:
        data = {
            "critical_missing": [],
            "important_missing": [],
            "ambiguous": [],
            "inconsistencies": [],
            "completeness_score": 80,
        }
    critical = data.get("critical_missing") or []
    important = data.get("important_missing") or []
    ambiguous = data.get("ambiguous") or []
    score = data.get("completeness_score", 0)
    has_gaps = len(critical) > 0 or len(important) > 0 or len(ambiguous) > 0
    return {
        "missing_fields": [m.get("field", "") for m in critical + important],
        "ambiguous_fields": [a.get("field", "") for a in ambiguous],
        "validation_results": {
            "critical_missing": critical,
            "important_missing": important,
            "ambiguous": ambiguous,
            "inconsistencies": data.get("inconsistencies", []),
            "completeness_score": score,
        },
        "questions": _to_questions(critical, important, ambiguous),
        "status": "questioning" if has_gaps else "generating",
    }


def _to_questions(
    critical: list[dict],
    important: list[dict],
    ambiguous: list[dict],
) -> list[dict[str, Any]]:
    qs = []
    for i, m in enumerate(critical):
        qs.append({
            "id": f"critical_{i}",
            "field": m.get("field", ""),
            "question": m.get("suggested_question", "Please specify."),
            "type": "text",
            "options": [],
            "required": True,
            "answered": False,
        })
    for i, m in enumerate(important):
        qs.append({
            "id": f"important_{i}",
            "field": m.get("field", ""),
            "question": m.get("suggested_question", "Please specify."),
            "type": "text",
            "options": [],
            "required": False,
            "answered": False,
        })
    for i, a in enumerate(ambiguous):
        qs.append({
            "id": f"ambiguous_{i}",
            "field": a.get("field", ""),
            "question": a.get("suggested_question", "Please choose."),
            "type": "single_choice",
            "options": a.get("options", []),
            "required": True,
            "answered": False,
        })
    return qs
