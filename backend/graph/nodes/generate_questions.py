from typing import Any

from backend.graph.state import PromptBuilderState


def generate_questions_node(state: PromptBuilderState) -> dict[str, Any]:
    """Already built in analyze_completeness; this node just ensures questions are in state."""
    questions = state.get("questions") or []
    return {
        "questions": questions,
        "status": "questioning",
    }
