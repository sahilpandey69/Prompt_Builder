import base64
import uuid
import time

import streamlit as st

from services.api_client import (
    create_prompt,
    answer_questions,
    get_result,
    submit_feedback,
)


def _auth_headers() -> dict[str, str]:
    import os
    token = os.environ.get("SIMPLE_PASSWORD", "")
    return {"X-Auth-Token": token}


def show_prompt_builder() -> None:
    st.title("🤖 Voice Agent Prompt Builder")

    if "stage" not in st.session_state:
        # Wizard stages:
        # 1) input  -> collect raw scripts / upload
        # 2) questions -> clarification Q&A
        # 3) generating -> backend generation progress
        # 4) preview -> final prompt + debug
        st.session_state.stage = "input"
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = {}
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "final_prompt" not in st.session_state:
        st.session_state.final_prompt = ""
    if "validation_results" not in st.session_state:
        st.session_state.validation_results = {}
    # For combined-input flow
    if "combined_file" not in st.session_state:
        st.session_state.combined_file = None
    if "combined_paste" not in st.session_state:
        st.session_state.combined_paste = ""

    # Wizard-specific state: structured per-section inputs and base template
    if "section_inputs" not in st.session_state:
        st.session_state.section_inputs = {
            "identity": "",
            "language_guidelines": "",
            "core_communication": "",
            "company_info": "",
            "tools": "",
            "conversation_flow": "",
            "objection_handling": "",
            "guardrails": "",
            "context_user_data": "",
        }
    if "base_template" not in st.session_state:
        st.session_state.base_template = ""

    if st.session_state.stage == "input":
        _show_input_stage()
    elif st.session_state.stage == "questions":
        _show_questions_stage()
    elif st.session_state.stage == "generating":
        _show_generating_stage()
    else:
        _show_preview_stage()


def _show_input_stage() -> None:
    st.subheader("📝 Step 1: Provide Client Requirements")
    mode = st.radio(
        "Choose how you want to provide requirements:",
        ["Guided sections (recommended)", "Upload / Paste script only"],
        horizontal=True,
    )

    if mode == "Guided sections (recommended)":
        _show_guided_wizard_inputs()
    else:
        _show_legacy_inputs()


def _show_legacy_inputs() -> None:
    """Legacy three-tab mode: upload, paste, or simple form.

    Kept for convenience, but the guided wizard is the primary path now.
    """
    tab1, tab2, tab3 = st.tabs(["📎 Upload File", "✍️ Paste Script", "📋 Simple Form"])

    with tab1:
        uploaded = st.file_uploader(
            "Upload client script or requirements",
            type=["txt", "pdf", "docx", "xlsx", "csv"],
            help="Supported: TXT, PDF, DOCX, XLSX, CSV",
        )
        if uploaded:
            raw_bytes = uploaded.read()
            ext = (uploaded.name or "").lower().split(".")[-1]
            if ext == "txt":
                raw = raw_bytes.decode("utf-8", errors="replace")
                st.success(f"Uploaded: {uploaded.name}")
                with st.expander("Preview"):
                    st.text_area("Content", raw, height=200, disabled=True)
                # Store for possible combined analysis; also allow file-only analysis
                st.session_state.combined_file = {
                    "content": raw,
                    "metadata": {"filename": uploaded.name, "file_type": ext, "kind": "text"},
                }
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Use in Combined Input", key="store_txt_file"):
                        st.toast("Text file stored for combined analysis.")
                with col2:
                    if st.button("🚀 Analyze File Only", type="primary", key="analyze_txt_file"):
                        _process_input(raw, "text")
                        st.rerun()
            else:
                b64 = base64.b64encode(raw_bytes).decode("ascii")
                st.success(f"Uploaded: {uploaded.name} ({len(raw_bytes)} bytes)")
                with st.expander("Preview"):
                    st.caption("Binary file; will be extracted on the server (PDF/DOCX/XLSX/CSV).")
                st.session_state.combined_file = {
                    "content": b64,
                    "metadata": {"filename": uploaded.name, "file_type": ext, "kind": "file"},
                }
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Use in Combined Input", key="store_bin_file"):
                        st.toast("File stored for combined analysis.")
                with col2:
                    if st.button("🚀 Analyze File Only", type="primary", key="analyze_bin_file"):
                        _process_input(
                            {"content": b64, "metadata": {"filename": uploaded.name, "file_type": ext}},
                            "file",
                        )
                        st.rerun()

    with tab2:
        script = st.text_area(
            "Paste your client script or requirements here",
            height=300,
            placeholder="Example:\nAgent: Maya from BrightBank\nPurpose: Loan reminder\n\nScript:\n'Hello, am I speaking with Mr. Sharma?'\n...",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Use in Combined Input", key="store_paste"):
                if not (script or "").strip():
                    st.error("Please paste some content first.")
                else:
                    st.session_state.combined_paste = script.strip()
                    st.toast("Pasted script stored for combined analysis.")
        with col2:
            if st.button("🚀 Analyze Script Only", type="primary", key="analyze_paste_only"):
                if not (script or "").strip():
                    st.error("Please paste some content.")
                else:
                    _process_input(script.strip(), "text")
                    st.rerun()

    with tab3:
        with st.form("structured_form_simple"):
            st.markdown("#### Basic Information")
            col1, col2 = st.columns(2)
            with col1:
                agent_name = st.text_input("Agent Name*", placeholder="e.g., Maya")
                company = st.text_input("Company Name*", placeholder="e.g., BrightBank")
            with col2:
                gender = st.selectbox("Gender*", ["Female", "Male"])
                use_case = st.selectbox(
                    "Use Case Type*",
                    ["Loan Reminder", "Appointment Booking", "Payment Collection", "Support Call", "Survey", "Custom"],
                )
            st.markdown("#### Language")
            default_lang = st.selectbox(
                "Default Language*",
                ["English", "Hindi", "Spanish", "Tamil", "Marathi", "Telugu"],
            )
            st.markdown("#### Call Flow")
            call_script = st.text_area(
                "Call Script/Flow*",
                height=200,
                placeholder="Describe the conversation flow...",
            )
            submitted = st.form_submit_button("🚀 Generate Prompt")
            if submitted:
                if not all([agent_name, company, default_lang, call_script]):
                    st.error("Please fill all required fields (*)")
                else:
                    form_content = {
                        "agent_name": agent_name,
                        "gender": gender.lower(),
                        "company": company,
                        "use_case": use_case,
                        "default_language": default_lang,
                        "call_script": call_script,
                    }
                    # Build combined input: file (if any) + pasted script (if any) + form data
                    combined_payload = {
                        "file": st.session_state.get("combined_file"),
                        "paste": st.session_state.get("combined_paste", "").strip() or None,
                        "form": form_content,
                    }
                    _process_input(combined_payload, "combined")
                    st.rerun()


def _show_guided_wizard_inputs() -> None:
    """New, section-based wizard that mirrors the production prompt structure."""
    st.markdown("#### Guided Section Inputs")

    with st.expander("1. Identity", expanded=True):
        st.markdown(
            "Define the agent persona: name, gender, seniority, role, goal, personality, and tone. "
            "Write it as you want it to appear under `# Identity`."
        )
        st.session_state.section_inputs["identity"] = st.text_area(
            "Identity section",
            value=st.session_state.section_inputs.get("identity", ""),
            height=160,
            placeholder="You are Chelsey, a professional, confident senior female AI phone agent...",
        )

    with st.expander("2. Language Guidelines"):
        st.markdown(
            "Specify default language, multilingual rules (implicit/explicit), language codes and "
            "any mixing rules (e.g. 30% English inside Spanish)."
        )
        st.session_state.section_inputs["language_guidelines"] = st.text_area(
            "Language Guidelines section",
            value=st.session_state.section_inputs.get("language_guidelines", ""),
            height=160,
            placeholder="# Language Guidelines\n- Default Language: English.\n- ...",
        )

    with st.expander("3. Core Communication Guidelines"):
        st.markdown(
            "Describe how the agent should speak: response length, fillers, empathy, and TTS rules "
            "(numbers, dates, %, acronyms, emails, etc.)."
        )
        st.session_state.section_inputs["core_communication"] = st.text_area(
            "Core Communication Guidelines section",
            value=st.session_state.section_inputs.get("core_communication", ""),
            height=200,
            placeholder="# Core Communication Guidelines\n1. Keep responses short...\n2. Convert all output into TTS-friendly form...\n...",
        )

    with st.expander("4. Company/Product Information"):
        st.markdown(
            "Paste or write the company / product overview, portfolio, plans, pricing tables, "
            "and value propositions."
        )
        st.session_state.section_inputs["company_info"] = st.text_area(
            "Company/Product Information section",
            value=st.session_state.section_inputs.get("company_info", ""),
            height=220,
            placeholder="# Company/Product Information\nWorkWise Compliance, previously Personnel Concepts, is a U.S.-based compliance solutions provider...\n...",
        )

    with st.expander("5. Tools"):
        st.markdown(
            "List all tools (built-in and custom), their purpose, parameters, and when they should be used "
            "(e.g. `hangup_call`, `transfer_call`, `calculate_billing_information_v3`, `press_digits`, etc.)."
        )
        st.session_state.section_inputs["tools"] = st.text_area(
            "Tools section",
            value=st.session_state.section_inputs.get("tools", ""),
            height=220,
            placeholder="# Tools\n- Use `hangup_call` to end the call.\n- Use `transfer_call` to connect to a human agent...\n...",
        )

    with st.expander("6. Conversation Flow"):
        st.markdown(
            "Define the full call flow in numbered, hierarchical form (1, 1.1, 1.2A, 1.2B, 2, 2.1...). "
            "Include branching, special paths (e.g. 0 employees, DNC, escalation), and explicit tool calls."
        )
        st.session_state.section_inputs["conversation_flow"] = st.text_area(
            "Conversation Flow section",
            value=st.session_state.section_inputs.get("conversation_flow", ""),
            height=260,
            placeholder="# Conversation Flow\n1. Call Opening...\n2. Purpose of call...\n3. Quick Account Questions...\n...",
        )

    with st.expander("7. Objection Handling"):
        st.markdown(
            "List out-of-flow objections (\"I'm busy\", \"Not interested\", DNC, price concerns, etc.) "
            "and the exact responses, in all relevant languages."
        )
        st.session_state.section_inputs["objection_handling"] = st.text_area(
            "Objection Handling section",
            value=st.session_state.section_inputs.get("objection_handling", ""),
            height=260,
            placeholder="# Objection Handling\n1. If user says \"I'm busy\"...\n2. If user says \"Not interested\"...\n...",
        )

    with st.expander("8. Guardrails"):
        st.markdown(
            "Define strict, non-negotiable rules (decision-maker checks, discount rules, "
            "multi-location coverage, flow completion before transfer, etc.)."
        )
        st.session_state.section_inputs["guardrails"] = st.text_area(
            "Guardrails section",
            value=st.session_state.section_inputs.get("guardrails", ""),
            height=220,
            placeholder="# Guardrails\n1. Always identify the decision maker before starting the call flow...\n...",
        )

    with st.expander("9. Context & User Data"):
        st.markdown(
            "List all dynamic variables and their meaning (e.g. {First_Name}, {Number_of_locations}, "
            "{Max_Allowed_Discount_%}, {current_timestamp}, etc.)."
        )
        st.session_state.section_inputs["context_user_data"] = st.text_area(
            "Context & User Data section",
            value=st.session_state.section_inputs.get("context_user_data", ""),
            height=200,
            placeholder="# Context & User Data\n- First name: {First_Name}\n- Number of locations: {Number_of_locations}\n...",
        )

    st.markdown("#### Optional: Base Template")
    st.caption(
        "If you already have a gold-standard prompt (like your existing WorkWise script), "
        "paste it here so the backend can use it as a style and structure reference."
    )
    st.session_state.base_template = st.text_area(
        "Base template (optional)",
        value=st.session_state.base_template,
        height=180,
        placeholder="Paste your gold prompt here to reuse its style and structure...",
    )

    if st.button("🚀 Generate Prompt from Sections", type="primary"):
        # Build a structured payload that the backend parser can consume.
        payload = {
            "mode": "section_wizard",
            "sections": st.session_state.section_inputs,
            "base_template": st.session_state.base_template or None,
        }
        _process_input(payload, "combined")
        st.rerun()


def _process_input(content: str | dict, input_type: str) -> None:
    try:
        if input_type == "form":
            res = create_prompt(st.session_state.session_id, "form", content)
        elif input_type == "combined":
            res = create_prompt(st.session_state.session_id, "combined", content)
        else:
            # text or file-only paths
            res = create_prompt(st.session_state.session_id, "text", content)
        st.session_state.session_id = res["session_id"]
        st.session_state.extracted_data = res.get("extracted_data", {})
        st.session_state.questions = res.get("questions", [])
        if res.get("status") == "needs_input" and st.session_state.questions:
            st.session_state.stage = "questions"
        else:
            # No questions or already complete
            if res.get("status") == "complete" or not st.session_state.questions:
                st.session_state.stage = "generating"
            else:
                st.session_state.stage = "questions"
    except Exception as e:
        st.error(f"Request failed: {e}")


def _show_questions_stage() -> None:
    st.subheader("❓ Step 2: Answer Clarification Questions")
    with st.expander("✅ What I found in your input", expanded=False):
        ex = st.session_state.extracted_data
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Agent Name", ex.get("agent_name") or "—")
            st.metric("Default Language", ex.get("default_language") or "—")
        with c2:
            st.metric("Company", ex.get("company_info") or "—")
            st.metric("Flow Steps", len(ex.get("flow_steps") or []))
        with c3:
            st.metric("Languages", len(ex.get("languages") or []))
            st.metric("Tools", len(ex.get("tools_needed") or []))

    questions = st.session_state.questions
    if not questions:
        st.info("No questions. Proceeding to generation.")
        st.session_state.stage = "generating"
        _run_generation()
        st.rerun()
        return

    answers = {}
    with st.form("answers_form"):
        for i, q in enumerate(questions):
            if q.get("answered"):
                continue
            st.markdown(f"**{i + 1}. {q.get('question', '')}**")
            if q.get("required"):
                st.caption("Required")
            qid = q.get("id", f"q{i}")
            qtype = q.get("type", "text")
            if qtype == "single_choice":
                opts = q.get("options") or ["Yes", "No"]
                answers[qid] = st.radio("Select", opts, key=f"q_{qid}")
            elif qtype == "multiple_choice":
                opts = q.get("options") or []
                answers[qid] = st.multiselect("Select", opts, key=f"q_{qid}")
            else:
                answers[qid] = st.text_input("Your answer", key=f"q_{qid}")
            st.divider()

        col1, _ = st.columns([1, 4])
        with col1:
            if st.form_submit_button("✅ Submit Answers", type="primary"):
                try:
                    res = answer_questions(st.session_state.session_id, answers)
                    st.session_state.session_id = res["session_id"]
                    st.session_state.questions = res.get("questions", [])
                    if res.get("status") == "complete":
                        st.session_state.stage = "generating"
                        _run_generation()
                    else:
                        st.session_state.questions = res.get("questions", [])
                    st.success("Answers submitted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Submit failed: {e}")
        if st.form_submit_button("⏭️ Skip & Generate"):
            try:
                answer_questions(st.session_state.session_id, {"_skip": "yes"})
                _run_generation()
                st.session_state.stage = "preview"
                st.rerun()
            except Exception as e:
                st.error(f"Skip failed: {e}")


def _run_generation() -> None:
    # If we already have final_prompt from a previous answer call, use result endpoint
    try:
        res = get_result(st.session_state.session_id)
        st.session_state.final_prompt = res.get("final_prompt", "")
        st.session_state.validation_results = res.get("validation_results", {})
        st.session_state.quality_score = res.get("quality_score", 0)
    except Exception:
        st.session_state.final_prompt = "# Identity\n(Generation in progress; run answer or create again if needed.)"
        st.session_state.validation_results = {}
        st.session_state.quality_score = 0
    st.session_state.stage = "preview"


def _show_generating_stage() -> None:
    st.subheader("⚙️ Step 3: Generating Your Prompt")
    progress_bar = st.progress(0)
    steps = [
        ("Analyzing completeness", 0.2),
        ("Generating Identity section", 0.35),
        ("Generating Language Guidelines", 0.5),
        ("Generating Conversation Flow", 0.7),
        ("Adding Tools & Guardrails", 0.85),
        ("Validating output", 1.0),
    ]
    for label, pct in steps:
        progress_bar.progress(pct)
        time.sleep(0.3)
    _run_generation()
    st.rerun()


def _show_preview_stage() -> None:
    st.subheader("✅ Step 4: Your Prompt is Ready!")
    vr = st.session_state.get("validation_results", {})
    score = st.session_state.get("quality_score") or vr.get("quality_score", 0)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Quality Score", f"{score}%", delta="Excellent" if score >= 90 else "Good" if score >= 80 else "Review")
    with c2:
        st.metric("Tokens", vr.get("tokens", 0))
    with c3:
        st.metric("Errors", len(vr.get("errors", [])))
    with c4:
        st.metric("Warnings", len(vr.get("warnings", [])))

    final = st.session_state.get("final_prompt", "")

    # Debug view: show raw extracted data and the final prompt side by side
    with st.expander("🔍 Debug View (input vs. output)", expanded=False):
        ex = st.session_state.get("extracted_data", {})
        st.markdown("**Extracted structured data (from parser):**")
        st.json(ex, expanded=False)
        st.markdown("**Final markdown prompt:**")
        st.code(final, language="markdown", line_numbers=True)

    # Main prompt display
    st.code(final, language="markdown", line_numbers=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            "⬇️ Download .md",
            final,
            file_name=f"prompt_{st.session_state.session_id[:8]}.md",
            mime="text/markdown",
            type="primary",
        )
    with col2:
        if st.button("📋 Copy to Clipboard"):
            st.toast("Copy the code block above (copy button in top-right of block).")
    with col3:
        if st.button("🔄 Regenerate"):
            st.session_state.stage = "generating"
            st.rerun()
    with col4:
        if st.button("🏠 Start Over"):
            st.session_state.stage = "input"
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.questions = []
            st.session_state.extracted_data = {}
            st.session_state.final_prompt = ""
            st.session_state.validation_results = {}
            st.rerun()

    st.divider()
    st.markdown("### Validation Report")
    section_scores = vr.get("section_scores") or {}
    if section_scores:
        cols = st.columns(min(len(section_scores), 4))
        for i, (name, sc) in enumerate(section_scores.items()):
            cols[i % len(cols)].metric(name.replace("_", " ").title(), f"{sc} pts")
    if vr.get("errors"):
        st.error("Errors:")
        for e in vr["errors"]:
            st.markdown(f"- {e}")
    if vr.get("warnings"):
        st.warning("Warnings:")
        for w in vr["warnings"]:
            st.markdown(f"- {w}")
    if vr.get("suggestions"):
        st.info("Suggestions:")
        for s in vr["suggestions"]:
            st.markdown(f"- {s}")
    if not vr.get("errors") and not vr.get("warnings"):
        st.success("No issues found. Prompt is production-ready.")

    st.markdown("### 📊 Feedback")
    with st.form("feedback_form"):
        deployed = st.checkbox("I deployed this to production")
        rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5)
        issues = st.text_area("Issues found (optional)", height=80)
        if st.form_submit_button("Submit Feedback"):
            try:
                submit_feedback(st.session_state.session_id, deployed, rating, issues)
                st.success("Thank you for your feedback!")
            except Exception as e:
                st.error(f"Feedback failed: {e}")
