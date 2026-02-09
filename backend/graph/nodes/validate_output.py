from typing import Any

from backend.graph.state import PromptBuilderState


def validate_output_node(state: PromptBuilderState) -> dict[str, Any]:
    final = state.get("final_prompt") or ""
    sections = state.get("sections_generated") or {}
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []
    section_scores: dict[str, Any] = {}

    # Structure (30 pts)
    required_sections = [
        "identity", "language_guidelines", "core_communication", "company_info",
        "tools", "conversation_flow", "objection_handling", "guardrails", "context_user_data",
    ]
    present = sum(1 for k in required_sections if sections.get(k) or (k.replace("_", " ").title() in final or f"# {k.replace('_', ' ').title()}" in final))
    section_scores["structure"] = min(30, present * 3)
    if present < 9:
        warnings.append(f"Only {present}/9 sections present.")

    # Identity (10 pts)
    has_identity = "# Identity" in final or "identity" in str(sections)
    has_goal = "goal" in final.lower() or "objective" in final.lower()
    section_scores["identity"] = 10 if (has_identity and has_goal) else (5 if has_identity else 0)
    if not has_identity:
        errors.append("Identity section missing.")

    # Language (10 pts)
    has_lang = "language" in final.lower() and ("default" in final.lower() or "guidelines" in final.lower())
    section_scores["language"] = 10 if has_lang else 5
    if not has_lang:
        warnings.append("Language guidelines missing or unclear.")

    # Flow (20 pts)
    has_flow = "Conversation Flow" in final or "conversation_flow" in str(sections)
    has_numbering = any(f"{i}." in final for i in range(1, 6))
    has_hangup = "hangup" in final.lower()
    section_scores["flow"] = (10 if has_flow else 0) + (5 if has_numbering else 0) + (5 if has_hangup else 0)
    if not has_flow:
        errors.append("Conversation Flow section missing.")
    if not has_hangup:
        warnings.append("hangup_call or end-call step not found.")

    # Tools (10 pts)
    has_tools = "# Tools" in final or "tools" in str(sections)
    section_scores["tools"] = 10 if (has_tools and has_hangup) else (5 if has_tools else 0)
    if not has_tools:
        warnings.append("Tools section missing.")

    # Objection handling (10 pts)
    has_objections = "Objection" in final or "objection_handling" in str(sections)
    section_scores["objection_handling"] = 10 if has_objections else 5
    if not has_objections:
        suggestions.append("Consider adding objection handling section.")

    # Guardrails (5 pts)
    has_guardrails = "Guardrail" in final or "guardrails" in str(sections)
    section_scores["guardrails"] = 5 if has_guardrails else 0
    if not has_guardrails:
        warnings.append("Guardrails section missing.")

    # Communication (5 pts)
    has_comms = "Core Communication" in final or "short" in final.lower() or "TTS" in final
    section_scores["communication"] = 5 if has_comms else 0

    total = sum(section_scores.values())
    quality_score = min(100, total)
    if errors:
        quality_score = max(0, quality_score - 10 * len(errors))

    prev_validation = state.get("validation_results") or {}
    return {
        "validation_results": {
            **prev_validation,
            "all_sections": present >= 6,
            "flow_complete": has_flow and has_hangup,
            "tool_consistency": has_tools,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "quality_score": quality_score,
            "section_scores": section_scores,
            "tokens": len(final.split()),
            "time_seconds": 0,
        },
        "quality_score": quality_score,
        "status": "complete",
    }
