from __future__ import annotations

import json
import os
from typing import Any

from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)


def _has_gemini_config() -> bool:
    s = get_settings()
    return bool(
        s.gemini_project_id
        and s.gemini_client_email
        and s.gemini_private_key
    )


def _has_azure_config() -> bool:
    s = get_settings()
    return bool(s.azure_openai_api_key and s.azure_openai_endpoint)


def _call_gemini(system_prompt: str, user_content: str) -> str:
    """
    Call Gemini via google-genai Client using the same pattern as the evaluator project:
    - service account from GEMINI_* env
    - vertexai=True
    - location typically 'global'
    - model name from GEMINI_MODEL (e.g. 'gemini-3-flash-preview')
    """
    s = get_settings()
    from google.oauth2 import service_account
    from google import genai
    from google.genai import types

    # Build service account info from env (same shape as CTO's EnvSettings.GEMINI_SERVICE_ACCOUNT_INFO)
    info = {
        "type": os.getenv("GEMINI_TYPE", "service_account"),
        "project_id": s.gemini_project_id,
        "private_key_id": os.getenv("GEMINI_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GEMINI_PRIVATE_KEY"),
        "client_email": os.getenv("GEMINI_CLIENT_EMAIL"),
        "client_id": os.getenv("GEMINI_CLIENT_ID"),
        "auth_uri": os.getenv("GEMINI_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("GEMINI_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv("GEMINI_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
        "client_x509_cert_url": os.getenv("GEMINI_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("GEMINI_UNIVERSE_DOMAIN", "googleapis.com"),
    }
    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    project = s.gemini_project_id
    location = s.gemini_location or "global"
    model_name = s.gemini_model or "gemini-3-flash-preview"

    logger.info("LLM: calling google-genai Gemini model=%s location=%s", model_name, location)
    client = genai.Client(
        project=project,
        location=location,
        credentials=credentials,
        api_key=None,
        vertexai=True,
    )

    # Combine system + user for single-turn generation
    combined = f"{system_prompt}\n\n---\n\nUser input:\n{user_content}"

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=combined)],
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="text/plain",
            temperature=0.2,
        ),
    )
    text = (response.text or "").strip()
    logger.info("LLM: google-genai Gemini returned %d chars", len(text))
    return text


def _call_azure(system_prompt: str, user_content: str) -> str:
    """Call Azure OpenAI (gpt-4.1 or deployment name from env)."""
    import openai
    s = get_settings()
    logger.info("LLM: calling Azure OpenAI deployment=%s", s.azure_openai_deployment_name or "gpt-4.1")
    client = openai.AzureOpenAI(
        api_key=s.azure_openai_api_key,
        api_version=s.azure_openai_api_version or "2024-12-01-preview",
        azure_endpoint=s.azure_openai_endpoint,
    )
    deployment = s.azure_openai_deployment_name or "gpt-4.1"
    resp = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    text = (resp.choices[0].message.content or "").strip()
    logger.info("LLM: Azure OpenAI returned %d chars", len(text))
    return text


def call_llm(system_prompt: str, user_content: str) -> str:
    """Use Gemini (Vertex) if GEMINI_* set, else Azure OpenAI if AZURE_* set, else mock."""
    if _has_gemini_config():
        try:
            return _call_gemini(system_prompt, user_content)
        except Exception as e:
            logger.exception("LLM: Gemini call failed, falling back. Error: %s", e)
            if _has_azure_config():
                try:
                    return _call_azure(system_prompt, user_content)
                except Exception:
                    logger.exception("LLM: Azure fallback after Gemini failed also failed")
            return _mock_completion(system_prompt, user_content, error=str(e))
    if _has_azure_config():
        try:
            return _call_azure(system_prompt, user_content)
        except Exception as e:
            logger.exception("LLM: Azure call failed, falling back to mock. Error: %s", e)
            return _mock_completion(system_prompt, user_content, error=str(e))
    logger.warning("LLM: no Gemini or Azure config found, using mock completion")
    return _mock_completion(system_prompt, user_content)


def _mock_completion(system_prompt: str, user_content: str, error: str | None = None) -> str:
    """Return mock structured output when no LLM is configured."""
    if "extract" in system_prompt.lower() or "parse" in system_prompt.lower():
        return json.dumps({
            "agent_name": "Maya",
            "agent_gender": "female",
            "default_language": "English",
            "languages": ["English"],
            "flow_steps": [
                {"step": "1", "dialogue": "Hello, am I speaking with the customer?", "condition": "Always", "language": "en"},
                {"step": "2", "dialogue": "This is Maya from BrightBank. Your loan has been approved.", "condition": "If yes", "language": "en"},
            ],
            "variables": ["customer_name", "loan_amount"],
            "tools_needed": ["hangup_call"],
            "company_info": "BrightBank",
        })
    if "completeness" in system_prompt.lower() or "missing" in system_prompt.lower():
        return json.dumps({
            "critical_missing": [],
            "important_missing": [{"field": "call_objective", "reason": "Unclear", "suggested_question": "What is the primary goal of this call?"}],
            "ambiguous": [],
            "inconsistencies": [],
            "completeness_score": 85,
        })
    if "generate" in system_prompt.lower() or "section" in system_prompt.lower():
        return json.dumps({
            "identity": "# Identity\nYou are Maya, a female voice AI agent for BrightBank.",
            "language_guidelines": "# Language Guidelines\n- Default Language: English.",
            "core_communication": "# Core Communication Guidelines\n1. Keep responses short.",
            "company_info": "# Company Information\nBrightBank.",
            "tools": "# Tools\n- Use `hangup_call` to end the call.",
            "conversation_flow": "# Conversation Flow\n1. Greeting\n2. Main message\n3. Closing",
            "objection_handling": "# Objection Handling\n1. If busy: offer to call back.",
            "guardrails": "# Guardrails\n1. Verify identity before sharing details.",
            "context_user_data": "# Context & User Data\n- customer_name, loan_amount",
        })
    return json.dumps({"error": error or "No API key", "fallback": "mock"})
