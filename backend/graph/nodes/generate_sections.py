import json
from typing import Any

from backend.graph.state import PromptBuilderState
from backend.llm import call_llm
from backend.llm.prompts import GENERATOR_SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)


def generate_sections_node(state: PromptBuilderState) -> dict[str, Any]:
    extracted = state.get("extracted_data") or {}
    answers = state.get("client_answers") or {}
    # Merge answers into a single context string
    context = (
        "You are generating the final voice agent prompt sections.\n\n"
        "Extracted data (from parser):\n"
        f"{json.dumps(extracted, indent=2)}\n\n"
        "User answers (clarifications):\n"
        f"{json.dumps(answers, indent=2)}"
    )
    try:
        out = call_llm(GENERATOR_SYSTEM_PROMPT, context)
        if out.startswith("```"):
            out = out.split("```", 2)[1]
            if out.startswith("json"):
                out = out[4:]
        sections = json.loads(out.strip())
    except Exception as e:
        logger.exception("Generator LLM JSON parse failed, using default sections. Error: %s. Raw output (truncated): %s", e, (out[:500] if isinstance(out, str) else out))
        sections = _default_sections(extracted)
    # Always join sections in the canonical order so the final prompt
    # matches the expected WorkWise-style structure.
    parts = [
        sections.get("identity", "# Identity\n(Generated)"),
        sections.get("language_guidelines", "# Language Guidelines\n- Default: English."),
        sections.get("core_communication", "# Core Communication Guidelines\n1. Keep responses short."),
        sections.get("company_info", "# Company/Product Information\n(From input)"),
        sections.get("tools", "# Tools\n- Use `hangup_call` to end the call."),
        sections.get("conversation_flow", "# Conversation Flow\n1. Greeting 2. Main 3. Closing"),
        sections.get("objection_handling", "# Objection Handling\n1. If busy: offer to call back."),
        sections.get("guardrails", "# Guardrails\n1. Verify identity. 2. No sensitive data."),
        sections.get("context_user_data", "# Context & User Data\n- Variables from flow."),
    ]
    final_prompt = "\n\n".join(parts)
    return {
        "sections_generated": sections,
        "final_prompt": final_prompt,
        "status": "validating",
    }


def _default_sections(extracted: dict) -> dict[str, str]:
    name = extracted.get("agent_name") or "Agent"
    gender = extracted.get("agent_gender") or "female"
    company = extracted.get("company_info") or "Company"
    return {
        "identity": (
            "# Identity\n"
            f"You are {name}, a {gender} voice AI agent on a phone call with the customer. "
            f"You work for {company}."
        ),
        "language_guidelines": "# Language Guidelines\n- Default Language: English.",
        "core_communication": (
            "# Core Communication Guidelines\n"
            "1. Keep responses short (around 15 words).\n"
            "2. Use natural fillers like \"um\", \"okay\", \"you know\".\n"
            "3. Convert all output into TTS-friendly spoken form (expand dates, numbers, and acronyms).\n"
        ),
        "company_info": f"# Company/Product Information\n{company}.",
        "tools": "# Tools\n- Use `hangup_call` to end the call.",
        "conversation_flow": (
            "# Conversation Flow\n"
            "1. Greeting & identity verification\n"
            "2. Explain purpose of call\n"
            "3. Ask required questions\n"
            "4. Summarize and close using `hangup_call`.\n"
        ),
        "objection_handling": (
            "# Objection Handling\n"
            "1. If the user is busy: acknowledge and offer a quick version or a callback.\n"
            "2. If the user does not understand: clarify briefly in simple language.\n"
        ),
        "guardrails": (
            "# Guardrails\n"
            "1. Verify identity before sharing any account details.\n"
            "2. Never ask for or repeat full card numbers, CVV, or OTP.\n"
            "3. Follow the conversation flow and complete closing before ending the call.\n"
        ),
        "context_user_data": (
            "# Context & User Data\n"
            "- {customer_name}\n"
            "- {current_timestamp}\n"
        ),
    }
