import json
from typing import Any

from backend.graph.state import PromptBuilderState
from backend.llm import call_llm
from backend.llm.prompts import PARSER_SYSTEM_PROMPT
from backend.utils.tool_detection import detect_tools_from_text, detect_tools_from_flow_steps
import logging

logger = logging.getLogger(__name__)


def parse_input_node(state: PromptBuilderState) -> dict[str, Any]:
    raw = (state.get("raw_input") or "").strip()
    if not raw:
        return {
            "extracted_data": {},
            "status": "parsing",
        }
    try:
        out = call_llm(PARSER_SYSTEM_PROMPT, raw)
        if out.startswith("```"):
            out = out.split("```", 2)[1]
            if out.startswith("json"):
                out = out[4:]
        data = json.loads(out.strip())
    except Exception as e:
        logger.exception("Parser LLM JSON parse failed, using fallback. Error: %s. Raw output (truncated): %s", e, (out[:500] if isinstance(out, str) else out))
        # Minimal but structurally compatible fallback.
        # This matches the PromptSpec-style shape expected downstream,
        # while still exposing convenience fields used by the UI/validator.
        data = {
            "agent_name": None,
            "agent_gender": None,
            "default_language": "English",
            "languages": ["English"],
            "flow_steps": [],
            "variables": [],
            "tools_needed": ["hangup_call"],
            "company_info": None,
            # Section scaffolding for downstream generator
            "identity": None,
            "language_guidelines": None,
            "core_communication": None,
            "company_product_information": None,
            "tools_section": None,
            "conversation_flow_section": None,
            "objection_handling": None,
            "guardrails": None,
            "context_user_data": None,
        }
    # Enrich tools from flow text if not set
    if not data.get("tools_needed") or data.get("tools_needed") == ["hangup_call"]:
        detected = detect_tools_from_flow_steps(data.get("flow_steps") or [])
        if not detected:
            detected = detect_tools_from_text(raw)
        data["tools_needed"] = list(dict.fromkeys(detected))
    return {
        "extracted_data": data,
        "status": "analyzing",
    }
