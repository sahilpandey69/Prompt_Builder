from typing import Literal

from langgraph.graph import START, END, StateGraph

from backend.graph.state import PromptBuilderState
from backend.graph.nodes import (
    parse_input_node,
    analyze_completeness_node,
    generate_questions_node,
    generate_sections_node,
    validate_output_node,
)


def _route_after_start(state: PromptBuilderState) -> Literal["parse_input", "generate_sections"]:
    """If we have client_answers, skip to generation; else parse."""
    if state.get("client_answers"):
        return "generate_sections"
    return "parse_input"


def _route_after_analyze(state: PromptBuilderState) -> Literal["generate_questions", "generate_sections"]:
    """If status is questioning, ask; else generate."""
    if state.get("status") == "questioning":
        return "generate_questions"
    return "generate_sections"


def get_graph():
    builder = StateGraph(PromptBuilderState)

    builder.add_node("parse_input", parse_input_node)
    builder.add_node("analyze_completeness", analyze_completeness_node)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("generate_sections", generate_sections_node)
    builder.add_node("validate_output", validate_output_node)

    builder.add_conditional_edges(START, _route_after_start, {
        "parse_input": "parse_input",
        "generate_sections": "generate_sections",
    })
    builder.add_edge("parse_input", "analyze_completeness")
    builder.add_conditional_edges("analyze_completeness", _route_after_analyze, {
        "generate_questions": "generate_questions",
        "generate_sections": "generate_sections",
    })
    builder.add_edge("generate_questions", END)
    builder.add_edge("generate_sections", "validate_output")
    builder.add_edge("validate_output", END)

    return builder.compile()
