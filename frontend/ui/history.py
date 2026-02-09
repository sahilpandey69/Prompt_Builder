import streamlit as st

from services.api_client import get_history, get_result


def show_history() -> None:
    st.title("🕒 History")
    try:
        sessions = get_history()
    except Exception as e:
        st.error(f"Could not load history: {e}")
        return
    if not sessions:
        st.info("No completed prompts yet. Create a prompt from 'New Prompt'.")
        return
    for item in sessions:
        sid = item.get("session_id", "")
        score = item.get("quality_score", 0)
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"Session: {sid[:16]}...")
                st.caption(f"Quality score: {score}%")
            with col2:
                if st.button("View", key=f"view_{sid}"):
                    try:
                        res = get_result(sid)
                        st.session_state.history_view_session = sid
                        st.session_state.history_view_prompt = res.get("final_prompt", "")
                        st.session_state.history_view_score = res.get("quality_score", 0)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    if st.session_state.get("history_view_prompt"):
        st.divider()
        st.subheader("Preview")
        st.metric("Quality Score", f"{st.session_state.get('history_view_score', 0)}%")
        st.code(st.session_state.history_view_prompt, language="markdown", line_numbers=True)
        if st.button("Close preview"):
            del st.session_state["history_view_prompt"]
            del st.session_state["history_view_session"]
            del st.session_state["history_view_score"]
            st.rerun()
