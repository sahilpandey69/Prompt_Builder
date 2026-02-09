# PRD Comparison & Setup Guide

## 1. PRD vs Implementation – What’s Covered

### 1.1 Input Processing (PRD §4.1)

| PRD Requirement | Status | Notes |
|-----------------|--------|--------|
| Plain text scripts | Done | Paste tab + text type in API |
| PDF uploads | Done | `file_extraction.py` + base64 upload |
| Excel/CSV | Done | pandas in `file_extraction.py` |
| Form-based input | Done | Form tab + form type in API |
| Word (.docx) | Done | python-docx in `file_extraction.py` |
| File size 10MB | Done | `MAX_SIZE_BYTES` in backend |
| UTF-8 / supported languages | Done | UTF-8 decode; languages in form dropdown (EN, HI, ES, TA, MR, TE) |
| **Images (OCR)** | **Not implemented** | PRD “SHOULD HAVE”; pytesseract in requirements but not wired |
| **Audio (transcription)** | **Not implemented** | PRD “SHOULD HAVE” |

### 1.2 Knowledge Extraction & Reasoning (PRD §4.2)

| PRD Requirement | Status |
|-----------------|--------|
| Base template (9 sections) | Done |
| Map inputs to template sections | Done (parser + reasoning nodes) |
| Detect missing critical/important/ambiguous | Done |
| Validate logical consistency | Done (reasoning agent) |
| Prioritised follow-up questions | Done |
| Question templates (critical/clarification/ambiguity) | Done (analyze_completeness → questions) |

### 1.3 Prompt Generation (PRD §4.3)

| PRD Requirement | Status |
|-----------------|--------|
| Section-by-section generation | Done (Identity, Language, Core Communication, Company, Tools, Flow, Objection, Guardrails, Context) |
| Identity / Language / Core Communication rules | Done (generator prompt + defaults) |
| Conversation flow with numbering (1, 1.1, 1.2A) | Done (generator instructions) |
| Tool auto-detection | Done (`tool_detection.py` + parser enrichment) |
| Objection handling | Done |
| Guardrails | Done |
| Context & User Data (variables) | Done |
| Quality validation before output | Done (`validate_output` node) |
| Quality score (100-point style) | Done (section_scores + quality_score) |

### 1.4 User Interface (PRD §4.4)

| PRD Requirement | Status | Notes |
|-----------------|--------|--------|
| Upload / Paste / Form tabs | Done | |
| “What I found” + clarification questions | Done | Questions stage |
| Progress indicator | Done | Generating stage |
| Prompt preview + quality report | Done | Preview with section scores, errors, warnings |
| Copy / Download .md | Done | |
| Regenerate / Start over | Done | |
| Feedback after use | Done | Feedback form in preview |
| **Deploy to Agent** | **Partial** | Backend: `POST .../deploy` (webhook). No “Deploy” button in Streamlit yet |
| **Edit Manually (with diff)** | **Not implemented** | PRD “Edit Manually: Open in editor (with diff tracking)” |
| **Save as Template** (UI) | **Partial** | Backend endpoint exists; no “Save as Template” button in preview |

### 1.5 API (PRD §5.5)

| Endpoint | Status |
|----------|--------|
| POST /api/v1/prompt/create | Done |
| POST /api/v1/prompt/answer | Done |
| GET /api/v1/prompt/{session_id}/result | Done |
| POST /api/v1/prompt/{session_id}/feedback | Done |
| GET /api/v1/templates | Done |
| POST /api/v1/prompt/from-template | Done |
| **Extra:** POST /api/v1/prompt/batch | Done |
| **Extra:** POST .../save-as-template | Done |
| **Extra:** POST .../deploy | Done |
| **Extra:** GET /api/v1/prompt/history | Done |
| **Extra:** GET /api/v1/analytics/feedback-summary | Done |

### 1.6 Technical Stack (PRD §5.4)

| Component | PRD | Implementation |
|-----------|-----|----------------|
| Frontend | Streamlit | Done |
| Backend | FastAPI | Done |
| Orchestration | LangGraph | Done |
| LLM | “Azure OpenAI (Gemini 3 Pro via API)” | **Azure OpenAI with `gpt-4o`** (see Env below for Gemini note) |
| Session | Redis | Done (optional; in-memory fallback) |
| Templates | MongoDB | Done (optional; in-memory fallback) |
| Feedback | PostgreSQL | Done (optional; table auto-created if DSN set) |
| Validation | Pydantic v2 | Done |

### 1.7 Security (PRD §6.3 – simplified per your request)

| Requirement | Status |
|-------------|--------|
| Single password from env | Done (`SIMPLE_PASSWORD`) |
| No RBAC / no audit logs | As requested |

---

## 2. What’s Still Missing or Optional

**Optional / “SHOULD HAVE” (not blocking):**

- **OCR for images** – Add image upload and call pytesseract in `file_extraction.py` if you need it.
- **Audio + transcription** – Would require a transcription service (e.g. Whisper API); not implemented.
- **Edit Manually with diff** – Would need an editor view and diff storage; not implemented.
- **Streamlit “Deploy” button** – Backend is ready; add a button in preview that calls `POST .../deploy`.
- **Streamlit “Save as Template” button** – Backend is ready; add a button that calls `POST .../save-as-template` with name/description.

**PRD “Gemini 3 Pro”:**  
The app currently uses **Azure OpenAI** (`gpt-4o`). To use Gemini instead you’d add a separate client (e.g. Google AI SDK) and switch `call_llm()` by env (e.g. `LLM_PROVIDER=gemini`). Not done; env below assumes Azure OpenAI.

**Quality checklist (Appendix 11.3):**  
We use a similar section-based score (structure, identity, language, flow, tools, objections, guardrails, communication). The exact 100-point breakdown from the appendix is not implemented line-by-line; behaviour is aligned.

---

## 3. Environment Variables & What to Set

### 3.1 Copy example env

```bash
# From project root
copy .env.example .env   # Windows
# or
cp .env.example .env     # Linux/Mac
```

Then edit `.env` (and keep it out of version control).

---

### 3.2 Required for basic run

| Variable | Required? | Example | Purpose |
|----------|-----------|---------|---------|
| `SIMPLE_PASSWORD` | **Optional** | `mySecretPass123` | App password. If **empty or unset**, backend and frontend allow access without a password (dev only). Set for any real use. |

- **Backend:** reads `.env` via `python-dotenv` in `config.py` (when you run from project root).
- **Frontend:** load the same `.env` (e.g. run Streamlit from project root so `app.py`’s `load_dotenv` finds `../.env`, or set env in the shell).

---

### 3.3 LLM (Azure OpenAI)

| Variable | Required? | Example | Purpose |
|----------|-----------|---------|---------|
| `AZURE_OPENAI_API_KEY` | Optional | `your-key` | Azure OpenAI API key. |
| `AZURE_OPENAI_ENDPOINT` | Optional | `https://your-resource.openai.azure.com/` | Azure OpenAI endpoint. |

- If **both** are set: backend uses Azure OpenAI with model **`gpt-4o`** (see `backend/llm/client.py`).
- If **either is missing**: backend uses **mock** JSON so the flow runs without a real LLM (good for testing).

To use a different Azure model (e.g. another GPT-4 variant), change the `model=` argument in `backend/llm/client.py` (e.g. to your deployment name).

---

### 3.4 Backend URL (frontend only)

| Variable | Required? | Example | Purpose |
|----------|-----------|---------|---------|
| `PROMPT_BUILDER_API_URL` | Optional | `http://localhost:8000` | Backend base URL. Default: `http://localhost:8000`. Set when backend runs elsewhere (e.g. `http://192.168.1.10:8000`). |

Set this in the **same** env the Streamlit app uses (e.g. in `.env` at project root if that’s what the frontend loads).

---

### 3.5 Optional: persistence and deploy

| Variable | Required? | Example | Purpose |
|----------|-----------|---------|---------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Session store. If unset, sessions are in-memory (lost on restart). |
| `MONGO_URI` | No | `mongodb://localhost:27017/prompt_builder` | Templates DB. If unset, templates are in-memory (built-in BFSI list). |
| `POSTGRES_DSN` | No | `postgresql://user:password@localhost:5432/prompt_builder` | Feedback DB. If set, feedback is stored and `feedback` table is created if missing. |
| `DEPLOY_WEBHOOK_URL` | No | `https://your-voice-platform.com/api/import` | URL for “Deploy”. When set, `POST /api/v1/prompt/{session_id}/deploy` POSTs the prompt to this URL. |

---

## 4. Step-by-step setup

### 4.1 One-time: env and dependencies

1. **Create `.env`** (copy from `.env.example`).
2. Set at least:
   - `SIMPLE_PASSWORD=your_password` (or leave empty for dev with no password).
   - Optionally: `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` for real LLM.
3. **Install dependencies** (from project root):

   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional)** Start Redis / MongoDB / Postgres (e.g. with `infra/docker-compose.yml`) and set `REDIS_URL`, `MONGO_URI`, `POSTGRES_DSN` in `.env` if you want persistence.

---

### 4.2 Run backend

From **project root** (so `backend` is importable):

**Windows (PowerShell):**

```powershell
cd C:\Users\sahil pandey\OneDrive\Desktop\Prompt_Builder
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/Mac:**

```bash
cd /path/to/Prompt_Builder
export PYTHONPATH=$PWD
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will load `.env` from the current directory. Health: `http://localhost:8000/health`.

---

### 4.3 Run frontend (Streamlit)

Frontend must see the same env (especially `SIMPLE_PASSWORD` and `PROMPT_BUILDER_API_URL`). Easiest: run from **project root** and load `.env` there.

**Windows (PowerShell):**

```powershell
cd C:\Users\sahil pandey\OneDrive\Desktop\Prompt_Builder
$env:PYTHONPATH = (Get-Location).Path
# Optional: point to backend if not on same machine
# $env:PROMPT_BUILDER_API_URL = "http://localhost:8000"
streamlit run frontend/app.py
```

**Linux/Mac:**

```bash
cd /path/to/Prompt_Builder
export PYTHONPATH=$PWD
streamlit run frontend/app.py
```

If Streamlit runs from another folder, set `SIMPLE_PASSWORD` and `PROMPT_BUILDER_API_URL` in that environment (e.g. export in shell or in a `.env` next to `app.py` and load it in `app.py`).

---

### 4.4 Optional: Docker backend

From project root:

```bash
docker-compose -f infra/docker-compose.yml up -d redis mongodb postgres
# Then run backend locally with REDIS_URL, MONGO_URI, POSTGRES_DSN set in .env
# Or build and run backend in Docker too (see infra/Dockerfile.backend)
```

---

## 5. Quick reference: what to set in `.env`

**Minimal (run with mock LLM, no persistence):**

```env
SIMPLE_PASSWORD=changeme
```

**With real LLM (Azure OpenAI):**

```env
SIMPLE_PASSWORD=changeme
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

**Full (persistence + deploy):**

```env
SIMPLE_PASSWORD=changeme
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
REDIS_URL=redis://localhost:6379/0
MONGO_URI=mongodb://localhost:27017/prompt_builder
POSTGRES_DSN=postgresql://user:password@localhost:5432/prompt_builder
DEPLOY_WEBHOOK_URL=https://your-voice-platform.com/api/import
```

**Frontend (if backend is not on localhost:8000):**

```env
PROMPT_BUILDER_API_URL=http://your-backend-host:8000
```

---

## 6. Summary

- **Implemented:** Input (text, PDF, DOCX, XLSX, CSV, form), parsing, reasoning, questions, full prompt generation, validation, quality score, Streamlit UI (upload/paste/form, questions, preview, download, feedback), templates, history, batch, save-as-template, deploy webhook, feedback DB, analytics summary. Security: single password from env.
- **Not implemented (optional):** OCR for images, audio transcription, “Edit Manually” with diff, PRD’s exact 100-point checklist wording, Gemini as LLM. Optional UI: “Deploy” and “Save as Template” buttons in preview (backend is ready).
- **Setup:** Copy `.env.example` to `.env`, set `SIMPLE_PASSWORD` (and optionally Azure LLM, `PROMPT_BUILDER_API_URL`, Redis/Mongo/Postgres/DEPLOY_WEBHOOK_URL). Run backend with `PYTHONPATH=<project_root>` and `uvicorn backend.main:app --reload --port 8000`, then run Streamlit from project root with the same env.
