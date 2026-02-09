"""Rule-based scan for tool usage in flow text."""
import re
from typing import Any

# Keywords that map to known tools
TOOL_PATTERNS = [
    (r"\b(hang\s*up|end\s*call|disconnect)\b", "hangup_call"),
    (r"\b(transfer|connect\s*to|put\s*through)\b", "transfer_call"),
    (r"\b(send\s*message|whatsapp|sms)\b", "send_whatsapp_message"),
    (r"\b(press|ivr|dial|dtmf)\b", "press_digits"),
    (r"\b(switch\s*language|change\s*to\s*hindi|change\s*language)\b", "change_speech_language"),
    (r"\b(book\s*appointment|schedule)\b", "book_appointment"),
    (r"\b(get\s*slots|available\s*slots)\b", "get_available_slots"),
]


def detect_tools_from_text(text: str) -> list[str]:
    """Return list of tool names mentioned in text."""
    if not text:
        return []
    text_lower = text.lower()
    found = set()
    for pattern, tool_name in TOOL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.add(tool_name)
    # Always include hangup_call for voice agents
    found.add("hangup_call")
    return sorted(found)


def detect_tools_from_flow_steps(flow_steps: list[dict[str, Any]]) -> list[str]:
    """Scan flow_steps (from parser) for tool mentions."""
    tools = set()
    for step in flow_steps or []:
        dialogue = step.get("dialogue") or ""
        condition = step.get("condition") or ""
        tools.update(detect_tools_from_text(dialogue))
        tools.update(detect_tools_from_text(condition))
    tools.add("hangup_call")
    return sorted(tools)
