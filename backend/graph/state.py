from typing import Any, TypedDict


class PromptSpec(TypedDict, total=False):
    """
    Canonical, structured representation of everything needed to build
    a production-grade voice agent prompt.

    Each key corresponds to one top-level markdown section in the final prompt.
    The values are themselves structured objects so that upstream nodes
    (parser, reasoning, UI) can attach rich metadata instead of only raw text.
    """

    # High-level identity / persona information for the agent
    identity: dict[str, Any]

    # Language rules (default language, multilingual switching, tools, examples)
    language_guidelines: dict[str, Any]

    # How the agent should sound and speak (TTS rules, fillers, etiquette)
    core_communication: dict[str, Any]

    # Company and product portfolio information
    company_info: dict[str, Any]

    # Tool catalog plus usage / trigger rules
    tools: dict[str, Any]

    # Full conversation flow with branching, steps and tool call anchors
    conversation_flow: dict[str, Any]

    # Out-of-flow objections, triggers and pivot-back responses
    objection_handling: dict[str, Any]

    # Hard business / safety rules that must always be enforced
    guardrails: dict[str, Any]

    # Dynamic variables / context available to the agent at runtime
    context_user_data: dict[str, Any]


class PromptBuilderState(TypedDict, total=False):
    # Raw user input (uploaded file text, pasted script, or combined payload summary)
    raw_input: str
    file_type: str

    # Answers collected from the clarification questions stage
    client_answers: dict[str, Any]

    # Rich, structured representation of the prompt we are building
    extracted_data: PromptSpec

    # Analysis details from completeness / validation stages
    missing_fields: list[str]
    ambiguous_fields: list[str]

    # LLM-generated sections and validation metadata
    sections_generated: dict[str, str]
    validation_results: dict[str, Any]
    final_prompt: str
    quality_score: int
    questions: list[dict[str, Any]]
    iteration_count: int

    # Overall pipeline status:
    # parsing | analyzing | questioning | generating | validating | complete
    status: str
