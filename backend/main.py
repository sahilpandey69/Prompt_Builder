import base64
import os
import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status

from backend.utils.file_extraction import extract_file_content
from fastapi.middleware.cors import CORSMiddleware

from backend.config import check_password, get_settings
from backend.graph import get_graph
from backend.graph.state import PromptBuilderState
from backend.models.api import (
    CreateRequest,
    CreateResponse,
    AnswerRequest,
    AnswerResponse,
    ResultResponse,
    FeedbackRequest,
    TemplateItem,
    FromTemplateRequest,
)
from backend.services.sessions import (
    get_session,
    set_session,
    merge_session,
    list_session_ids,
)
from backend.services import (
    list_templates_svc,
    get_template,
    save_feedback,
    get_feedback_summary,
)

app = FastAPI(title="Prompt Builder API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def auth_dependency(
    x_auth_token: str | None = Header(default=None, alias="X-Auth-Token"),
):
    if not check_password(x_auth_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
        )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/ping", dependencies=[Depends(auth_dependency)])
async def ping():
    return {"message": "pong"}


def _get_content(req: CreateRequest) -> tuple[str, str]:
    inp = req.input
    t = inp.get("type", "text")
    if t == "text":
        content = inp.get("content")
        if content is None:
            return "", "text"
        return str(content).strip(), "text"
    if t == "combined":
        # Combined input: may contain file, paste, and form parts
        content = inp.get("content") or {}
        file_part = content.get("file")
        paste_text = (
            (content.get("paste") or "").strip() if isinstance(content, dict) else ""
        )
        form_part = content.get("form") or {}
        chunks: list[str] = []

        # File content (if any)
        if isinstance(file_part, dict) and file_part.get("content") is not None:
            meta = file_part.get("metadata") or {}
            filename = meta.get("filename") or "upload"
            kind = meta.get("kind") or "file"
            file_payload = file_part.get("content")
            try:
                if kind == "text":
                    file_text = str(file_payload)
                else:
                    # Assume base64-encoded bytes for binary files
                    raw_bytes = base64.b64decode(str(file_payload), validate=True)
                    file_text = extract_file_content(raw_bytes, filename)
                chunks.append(file_text)
            except Exception:
                # Fall back to raw string
                chunks.append(str(file_payload)[:10000])

        # Pasted script (if any)
        if paste_text:
            chunks.append(paste_text)

        # Form data (if any)
        if isinstance(form_part, dict) and form_part:
            parts = [f"{k}: {v}" for k, v in form_part.items()]
            chunks.append("Form Data:\n" + "\n".join(parts))

        combined_text = "\n\n---\n\n".join(chunks).strip()
        return combined_text, "combined"
    if t == "form":
        # Serialize form to a single text block for parser
        data = inp.get("content") or inp
        if isinstance(data, dict):
            parts = [f"{k}: {v}" for k, v in data.items()]
            return "\n".join(parts), "form"
        return str(data), "form"
    if t == "file":
        content = inp.get("content") or ""
        metadata = inp.get("metadata") or {}
        if isinstance(content, dict):
            metadata = content.get("metadata") or metadata
            content = content.get("content") or content
        filename = metadata.get("filename") or "upload"
        if isinstance(content, str):
            b64 = content.split(";base64,", 1)[1] if ";base64," in content else content
            try:
                raw_bytes = base64.b64decode(b64, validate=True)
                return extract_file_content(raw_bytes, filename), metadata.get(
                    "file_type"
                ) or (filename.split(".")[-1] if "." in filename else "file")
            except Exception:
                return content[:10000], metadata.get("file_type") or "text"
        return "", "file"
    return "", "text"


@app.post("/api/v1/prompt/create", response_model=CreateResponse)
async def prompt_create(
    body: CreateRequest,
    _: None = Depends(auth_dependency),
):
    session_id = body.session_id or str(uuid.uuid4())
    raw_input, file_type = _get_content(body)
    if not raw_input and body.input.get("type") != "form":
        raise HTTPException(status_code=400, detail="Input content is required")

    initial: PromptBuilderState = {
        "raw_input": raw_input,
        "file_type": file_type,
        "client_answers": {},
        "extracted_data": {},
        "questions": [],
        "iteration_count": 0,
        "status": "parsing",
    }
    set_session(session_id, initial)
    graph = get_graph()
    result = graph.invoke(initial, config={"configurable": {"thread_id": session_id}})

    # Result may be the last node's output; we need full state. LangGraph returns final state.
    state = result if isinstance(result, dict) else {}
    questions = state.get("questions") or []
    extracted = state.get("extracted_data") or {}
    status_val = state.get("status") or "parsed"
    completeness = (state.get("validation_results") or {}).get("completeness_score", 0)

    # Merge previous session state (if any) with latest graph state
    previous = get_session(session_id) or {}
    set_session(session_id, {**previous, **state})

    return CreateResponse(
        session_id=session_id,
        status="needs_input" if status_val == "questioning" else "parsed",
        questions=questions,
        extracted_data=extracted,
        completeness_score=completeness,
    )


@app.post("/api/v1/prompt/answer", response_model=AnswerResponse)
async def prompt_answer(
    body: AnswerRequest,
    _: None = Depends(auth_dependency),
):
    session_id = body.session_id
    existing = get_session(session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")

    merged = merge_session(session_id, {"client_answers": body.answers})
    graph = get_graph()
    result = graph.invoke(
        merged,
        config={"configurable": {"thread_id": session_id}},
    )
    state = result if isinstance(result, dict) else {}
    status_val = state.get("status") or "complete"
    questions = state.get("questions") or []
    previous = get_session(session_id) or {}
    set_session(session_id, {**previous, **state})

    progress = 100 if status_val == "complete" else 50
    return AnswerResponse(
        session_id=session_id,
        status="complete" if status_val == "complete" else "needs_input",
        questions=questions,
        progress=progress,
    )


@app.get("/api/v1/prompt/history")
async def prompt_history(_: None = Depends(auth_dependency)):
    ids = list_session_ids()
    # Return minimal info: session_id, and if we have final_prompt we consider it "complete"
    out = []
    for sid in ids[:100]:  # limit 100
        s = get_session(sid)
        if s and s.get("final_prompt"):
            out.append({"session_id": sid, "quality_score": s.get("quality_score", 0)})
    return {"sessions": out}


@app.get("/api/v1/prompt/{session_id}/result", response_model=ResultResponse)
async def prompt_result(
    session_id: str,
    _: None = Depends(auth_dependency),
):
    existing = get_session(session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")
    vr = existing.get("validation_results") or {}
    return ResultResponse(
        session_id=session_id,
        final_prompt=existing.get("final_prompt") or "",
        quality_score=existing.get("quality_score") or vr.get("quality_score", 0),
        validation_results=vr,
        metadata={
            "tokens": vr.get("tokens", 0),
            "time_seconds": vr.get("time_seconds", 0),
        },
    )


@app.post("/api/v1/prompt/{session_id}/feedback")
async def prompt_feedback(
    session_id: str,
    body: FeedbackRequest,
    _: None = Depends(auth_dependency),
):
    save_feedback(
        session_id, body.deployed, body.rating, body.issues, body.manual_edits
    )
    return {"session_id": session_id, "received": True}


@app.get("/api/v1/templates")
async def list_templates(_: None = Depends(auth_dependency)):
    return {"templates": list_templates_svc()}


@app.post("/api/v1/prompt/from-template")
async def from_template(
    body: FromTemplateRequest,
    _: None = Depends(auth_dependency),
):
    t = get_template(body.template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": t, "customizations": body.customizations}


# Batch: create multiple prompts from a list of inputs
@app.post("/api/v1/prompt/batch")
async def prompt_batch(
    body: dict[str, Any],  # { "inputs": [ { type, content, metadata? } ] }
    _: None = Depends(auth_dependency),
):
    inputs_list = body.get("inputs") or []
    if len(inputs_list) > 20:
        raise HTTPException(status_code=400, detail="Max 20 inputs per batch")
    session_ids = []
    graph = get_graph()
    for i, inp in enumerate(inputs_list):
        raw, file_type = _get_content(CreateRequest(session_id=None, input=inp))
        if not raw and inp.get("type") != "form":
            continue
        session_id = str(uuid.uuid4())
        initial: PromptBuilderState = {
            "raw_input": raw,
            "file_type": file_type,
            "client_answers": {},
            "extracted_data": {},
            "questions": [],
            "iteration_count": 0,
            "status": "parsing",
        }
        set_session(session_id, initial)
        result = graph.invoke(
            initial, config={"configurable": {"thread_id": session_id}}
        )
        state = result if isinstance(result, dict) else {}
        previous = get_session(session_id) or {}
        set_session(session_id, {**previous, **state})
        session_ids.append({"session_id": session_id, "index": i})
    return {"sessions": session_ids, "count": len(session_ids)}


# Save prompt as template (writes to MongoDB if connected)
@app.post("/api/v1/prompt/{session_id}/save-as-template")
async def save_as_template(
    session_id: str,
    body: dict[str, Any],  # { "name", "description", "category?", "language?" }
    _: None = Depends(auth_dependency),
):
    existing = get_session(session_id)
    if not existing or not existing.get("final_prompt"):
        raise HTTPException(status_code=404, detail="Session or final prompt not found")
    name = body.get("name") or f"Template {session_id[:8]}"
    description = body.get("description") or "Saved from prompt builder"
    template_id = (name.lower().replace(" ", "-")[:50]) or f"tpl-{session_id[:8]}"
    # If MongoDB connected, insert; else return template payload for frontend to display
    try:
        from pymongo import MongoClient

        uri = get_settings().mongo_uri
        if uri:
            client = MongoClient(uri)
            db = client.get_database("prompt_builder")
            coll = db.get_collection("templates")
            coll.update_one(
                {"id": template_id},
                {
                    "$set": {
                        "id": template_id,
                        "name": name,
                        "description": description,
                        "final_prompt": existing.get("final_prompt"),
                        "category": body.get("category", "BFSI"),
                        "language": body.get("language", "English"),
                        "use_count": 0,
                        "avg_rating": 0.0,
                    }
                },
                upsert=True,
            )
    except Exception:
        pass
    return {"template_id": template_id, "name": name, "description": description}


# Deploy hook: POST to configurable URL (env DEPLOY_WEBHOOK_URL)
@app.post("/api/v1/prompt/{session_id}/deploy")
async def deploy_prompt(
    session_id: str,
    _: None = Depends(auth_dependency),
):
    existing = get_session(session_id)
    if not existing or not existing.get("final_prompt"):
        raise HTTPException(status_code=404, detail="Session or final prompt not found")
    url = os.environ.get("DEPLOY_WEBHOOK_URL")
    if not url:
        raise HTTPException(status_code=501, detail="DEPLOY_WEBHOOK_URL not configured")
    try:
        import httpx

        r = httpx.post(
            url,
            json={
                "session_id": session_id,
                "final_prompt": existing.get("final_prompt"),
                "quality_score": existing.get("quality_score"),
            },
            timeout=30.0,
        )
        r.raise_for_status()
        return {"deployed": True, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Deploy failed: {e}")


# Analytics / learning: feedback summary (for A/B and versioning)
@app.get("/api/v1/analytics/feedback-summary")
async def feedback_summary(_: None = Depends(auth_dependency)):
    return get_feedback_summary()
