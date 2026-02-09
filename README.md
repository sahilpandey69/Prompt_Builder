# Voice Agent Prompt Builder

AI-powered prompt builder that turns client requirements into production-ready voice agent system prompts. Streamlit frontend + FastAPI + LangGraph backend.

## Setup

1. **Clone and install**
   ```bash
   cd Prompt_Builder
   pip install -r requirements.txt
   ```

2. **Environment**
   - Copy `.env.example` to `.env`
   - Set `SIMPLE_PASSWORD` for app access (optional; if unset, no password required for local dev)
   - Optionally set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` for real LLM; otherwise mock outputs are used.

3. **Run backend**
   ```bash
   # From project root; ensure PYTHONPATH includes project root
   set PYTHONPATH=%CD%   # Windows
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run frontend**
   ```bash
   cd frontend
   streamlit run app.py
   ```
   Or from project root: `streamlit run frontend/app.py` (ensure project root is on `PYTHONPATH` or run from `frontend`).

5. **API base URL**
   - Frontend calls `http://localhost:8000` by default. Override with `PROMPT_BUILDER_API_URL` if backend runs elsewhere.

## Flow

1. **New Prompt** → Upload script / paste text / fill form → Analyze.
2. If the backend needs clarifications, answer the questions (or click "Skip & Generate").
3. Prompt is generated and shown with quality score; download as `.md` or copy.

## Features

- **New Prompt**: Upload script (TXT/PDF/DOCX/XLSX/CSV), paste text, or fill a structured form. Backend parses with LLM (or mock), asks clarification questions, then generates a full voice-agent prompt with Identity, Language Guidelines, Core Communication, Conversation Flow, Tools, Objection Handling, Guardrails, and Context.
- **Templates**: List and use BFSI (and other) templates; "Use Template" switches to New Prompt (pre-fill in Phase 2).
- **History**: View past sessions and their results.
- **Feedback**: Submit rating and "deployed" flag per prompt; stored in Postgres when `POSTGRES_DSN` is set.
- **Batch**: `POST /api/v1/prompt/batch` with a list of inputs to create multiple prompts in one call.
- **Save as template**: `POST /api/v1/prompt/{session_id}/save-as-template` to save a generated prompt as a template (MongoDB when `MONGO_URI` is set).
- **Deploy hook**: Set `DEPLOY_WEBHOOK_URL`; `POST /api/v1/prompt/{session_id}/deploy` forwards the prompt to that URL.
- **Analytics**: `GET /api/v1/analytics/feedback-summary` returns deployed count, average rating, and total feedback count (Postgres).

## Security

- Single shared password via `SIMPLE_PASSWORD` in env. Frontend sends it as `X-Auth-Token`; backend validates on protected routes.
