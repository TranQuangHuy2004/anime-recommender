import streamlit as st
from streamlit_searchbox import st_searchbox
import utils.helpers as helper
from utils.session_manager import SessionManager


def render_search_bar(es_service):
    """
    Reusable search bar for Home + Search pages
    """

    # --- Search suggestions ---
    def get_search_suggestions(searchterm: str) -> list:
        if not searchterm or len(searchterm.strip()) < 2:
            return []
        return es_service.get_search_suggestions_for_streamlit(
            searchterm=searchterm,
            search_category=st.session_state.search_category,
            limit=15
        )

    # --- Unified submit handler ---
    def on_search_submit(value):
        if value is None:
            return

        # Raw text submitted via Enter
        if isinstance(value, str):
            query = value.strip()
            if query:
                # Set search parameters
                SessionManager.set('search_query', query)
                SessionManager.set('search_type', 'All')
                SessionManager.set('search_filters', {})
                SessionManager.set('sort_order', 'desc')
                SessionManager.set('sort_by', 'relevance')
                SessionManager.set('current_page', 1)
                st.switch_page("pages/2_🔍_Search.py")
            return

        # Raw search option
        if value.get("raw_search"):
            query = value["query"]
            if query:
                # Set search parameters
                SessionManager.set('search_query', query)
                SessionManager.set('search_type', 'All')
                SessionManager.set('search_filters', {})
                SessionManager.set('sort_order', 'desc')
                SessionManager.set('sort_by', 'relevance')
                SessionManager.set('current_page', 1)

                st.switch_page("pages/2_🔍_Search.py")
            return

        # Entity selected
        entity_type = value.get("raw_type", "").lower()
        if entity_type == "anime":
            # Set selected anime
            SessionManager.set_selected_anime(value["id"])
            # Clear search state
            SessionManager.set('search_query', '')
            SessionManager.set('search_type', 'All')
            SessionManager.set('search_filters', {})
            SessionManager.set('sort_order', 'desc')
            SessionManager.set('sort_by', 'relevance')
            SessionManager.set('current_page', 1)

            st.switch_page("pages/4_🎬_Anime_Details.py")
        else:
            helper.apply_filters({
                f"{value["category"].lower()}s": [value["name"]]
            }, SessionManager)

    # --- UI ---
    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        search_category_ui = st.selectbox(
            "Category",
            ["All", "Anime", "Studio", "Genre", "Theme", "Demographic"],
            label_visibility="collapsed",
            key="search_category_ui"
        )
        st.session_state.search_category = (
            "all" if search_category_ui == "All" else search_category_ui.lower()
        )

    with col2:
        placeholder = (
            "Search anime, characters, studios, genres..."
            if search_category_ui == "All"
            else f"Search {search_category_ui.lower()}..."
        )

        st_searchbox(
            search_function=get_search_suggestions,
            placeholder=placeholder,
            key="global_search_box",
            clear_on_submit=True,
            submit_function=on_search_submit,
            debounce=200,
            rerun_on_update=True,
        )

    with col3:
        if st.button("⚙️ Advanced Search", use_container_width=True):
            st.switch_page("pages/3_⚙️_Advanced_Search.py")
