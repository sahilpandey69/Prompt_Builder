import streamlit as st

from services.api_client import list_templates


def show_templates() -> None:
    st.title("📚 Prompt Templates")
    try:
        templates = list_templates()
    except Exception as e:
        st.error(f"Could not load templates: {e}")
        return
    if not templates:
        st.info("No templates yet. Create a prompt and save it as a template (coming in a later phase).")
        return
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("🔍 Search templates", placeholder="e.g., BFSI, loan, Hindi")
    with col2:
        category = st.selectbox("Category", ["All", "BFSI", "Healthcare", "Logistics", "Retail"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Most Used", "Highest Rated", "Recent"])
    filtered = templates
    if search:
        search_lower = search.lower()
        filtered = [t for t in filtered if search_lower in (t.get("name") or "").lower() or search_lower in (t.get("description") or "").lower()]
    if category != "All":
        filtered = [t for t in filtered if (t.get("category") or "BFSI") == category]
    cols = st.columns(2)
    for idx, template in enumerate(filtered):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"### {template.get('name', 'Unnamed')}")
                st.caption(template.get("description", ""))
                c1, c2, c3 = st.columns(3)
                c1.metric("Used", template.get("use_count", 0))
                c2.metric("Rating", f"{template.get('avg_rating', 0):.1f}⭐")
                c3.metric("Language", template.get("language", "English"))
                if st.button("✨ Use Template", key=f"use_{template.get('id', idx)}", type="primary"):
                    st.session_state.nav_selected = "New Prompt"
                    st.session_state.use_template_id = template.get("id")
                    st.session_state.use_template_name = template.get("name", "")
                    st.rerun()
    if st.session_state.get("use_template_id"):
        st.info(f"Template '{st.session_state.get('use_template_name', '')}' selected. Pre-fill from template will be available in Phase 2; for now create a new prompt and use the same structure.")
