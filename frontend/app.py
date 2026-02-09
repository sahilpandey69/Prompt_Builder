import os
import sys
import uuid

# Load .env from project root when running streamlit run frontend/app.py
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

import streamlit as st


APP_TITLE = "Voice Agent Prompt Builder"


def require_password() -> bool:
    stored = os.getenv("SIMPLE_PASSWORD", "").strip()
    if not stored:
        # If no password configured, allow access (dev convenience)
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title(APP_TITLE)
    st.subheader("Login")
    password = st.text_input("Enter access password", type="password")
    if st.button("Unlock"):
        if password == stored:
            st.session_state.authenticated = True
            st.success("Authenticated")
            st.experimental_rerun()
        else:
            st.error("Incorrect password")
    return False


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if not require_password():
        return

    with st.sidebar:
        nav_options = ["New Prompt", "Templates", "History", "Settings"]
        idx = nav_options.index(st.session_state.get("nav_selected", "New Prompt")) if st.session_state.get("nav_selected") in nav_options else 0
        selected = st.radio(
            "Prompt Builder",
            nav_options,
            index=idx,
            key="nav_radio",
        )
        if selected != st.session_state.get("nav_selected"):
            st.session_state.nav_selected = selected

    st.session_state.setdefault("session_id", str(uuid.uuid4()))

    if selected == "New Prompt":
        from ui.prompt_builder import show_prompt_builder
        show_prompt_builder()
    elif selected == "Templates":
        from ui.templates import show_templates
        show_templates()
    elif selected == "History":
        from ui.history import show_history
        show_history()
    else:
        st.title("⚙️ Settings")
        st.write("SIMPLE_PASSWORD is configured:", bool(os.getenv("SIMPLE_PASSWORD")))


if __name__ == "__main__":
    main()

