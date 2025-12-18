# pages/2_🔍_Search.py
import streamlit as st
from streamlit_theme import st_theme
from components.search_bar import render_search_bar
from components.anime_card import AnimeCard
from utils.session_manager import SessionManager

# Clear query params at start
st.query_params.clear()

# Detect current theme
theme = st_theme()

if theme and theme["base"] == "light":
    bg_color = "rgba(200, 200, 200, 0.75)"
    font_color = "rgba(0, 0, 0, 1)"
    border_card = "rgba(0, 0, 0, 0.2)"
    linear_gradient = "linear-gradient(rgba(200, 200, 200, 0.5), rgba(0, 0, 0, 0.75))"
    button_background = "rgba(255, 255, 255, 0.5)"
    anime_card_background = "rgba(255, 255, 255, 0.5)"
else:
    bg_color = "rgba(0, 0, 0, 0.5)"
    font_color = "rgba(255, 255, 255, 1)"
    border_card = "rgba(255, 255, 255, 0.5)"
    linear_gradient = "linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, .8))"
    button_background = ""
    anime_card_background = "rgba(0, 0, 0, 0)"

# Page configuration
st.set_page_config(
    page_title="Anime Recommendation System",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize services with caching
SessionManager()
SessionManager.init_search_state()

# Custom CSS
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: {linear_gradient},
                url('https://i.pinimg.com/736x/f8/a1/63/f8a16399295653c1522738948ba629d4.jpg');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
    color: {font_color};
}}
            
[data-testid="stMainBlockContainer"] {{
    background-color: {bg_color};
    border-radius: 30px;
    padding: 30px 50px;
    margin: 100px auto; 
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0);
    max-width: 1200px;
}}

[class*="st-key-individual_anime_card_"] [data-testid="stVerticalBlock"] {{
    gap: 0.5rem;
}}

# [class*="st-key-individual_anime_card_"]:hover {{
#     transition: transform 0.5s ease;
#     transform: scale(1.05);
# }}

[class*="st-key-individual_anime_card_"] button {{
    background-color: {button_background}
}}

[data-testid="stBaseButton-secondary"] {{
    background-color: {button_background}
    
}}

[data-testid="stSelectbox"] > div > div {{
    background-color: {button_background}
}}

[data-testid="stCustomComponentV1"] #root  {{
    background-color: {button_background}
}}

[data-testid="stMetricValue"] {{
    font-size: 1.5rem;
}}

</style>
""", unsafe_allow_html=True)


if st.button("🏠 Home"):
    st.switch_page("pages/1_🏠_Home.py")

title = ""
for key, value in st.session_state.search_filters.items():
    if isinstance(value, list):
        title += (f"{', '.join(value)} ")
    else:
        title += f"{value.title() if isinstance(value, str) else value} "
if title:
    st.title(f"{title}- Anime")
else:
    st.title("Popular Anime")

render_search_bar(st.session_state.es)

# Main content area
st.markdown("---")

# Sort and pagination controls
col_controls1, col_controls2, col_controls3 = st.columns([2, 1, 1])

with col_controls1:
    sort_options = {
        "Relevance": "_score",
        "Score": "score",
        "Popularity": "popularity",
        "Year": "year",
        "Episodes": "episodes",
        "Title": "title"
    }
    selected_sort_display = st.selectbox("Sort by", list(sort_options.keys()))
    st.session_state.sort_by = sort_options[selected_sort_display]

with col_controls2:
    if selected_sort_display.lower() != "relevance":  # Only show order options for non-relevance sorts
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])
    else:
        sort_order = st.selectbox("Order", ["Descending"])  # Fixed for relevance
    st.session_state.sort_order = "desc" if sort_order == "Descending" else "asc"

with col_controls3:
    results_per_page = st.selectbox("Results per page", [10, 20, 50, 100], index=0)

# Perform search based on current state
try:
    # Use advanced_search for custom sorting
    search_results = st.session_state.es.advanced_search(
        query=st.session_state.search_query,
        filters=st.session_state.search_filters,
        sort_by=st.session_state.sort_by,
        order=st.session_state.sort_order,
        page=st.session_state.current_page,
        size=results_per_page
    )

    total_results = search_results.get('total', 0)
    hits = search_results.get('hits', [])

    # Display results summary
    if total_results > 0:
        st.success(f"✅ Found **{total_results:,}** anime matching your criteria")

        # Calculate page info
        total_pages = max(1, (total_results + results_per_page - 1) // results_per_page)
        start_idx = (st.session_state.current_page - 1) * results_per_page + 1
        end_idx = min(st.session_state.current_page * results_per_page, total_results)

        st.caption(f"Showing results {start_idx:,} - {end_idx:,} of {total_results:,}")

        st.markdown("---")

        # Display anime cards
        anime_card = AnimeCard()
        for idx, anime in enumerate(hits):
            # Create a full-width container for each anime
            anime_card.create_anime_card_1(anime, "hit", idx)

            st.markdown("---")

        # Pagination controls
        if total_pages > 1:
            with st.container(key="pagination_container_top", horizontal=True):
                if st.button("⮜⮜", help="First") and st.session_state.current_page > 1:
                    st.session_state.current_page = 1
                    st.rerun()
                if st.button("⮜", help="Previous") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()

                page_options = list(range(1, min(total_pages, 20) + 1))
                if st.session_state.current_page > 20:
                    page_options = [st.session_state.current_page]

                new_page = st.selectbox(
                    "Page",
                    page_options,
                    index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0,
                    label_visibility="collapsed"
                )
                if new_page != st.session_state.current_page:
                    st.session_state.current_page = new_page
                    st.rerun()

                if st.button("⮞", help="Next") and st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()
                if st.button("⮞⮞", help="Last") and st.session_state.current_page < total_pages:
                    st.session_state.current_page = total_pages
                    st.rerun()

        # Bottom pagination (if many results)
        if total_pages > 1:
            st.markdown("---")
            st.write(f"**Page {st.session_state.current_page} of {total_pages}**")

    else:
        st.warning("⚠️ No results found. Try adjusting your search criteria.")
        if st.button("Clear search and filters"):
            st.session_state.search_query = ''
            st.session_state.search_filters = {}
            st.session_state.current_page = 1
            st.rerun()

except Exception as e:
    st.error(f"Error performing search: {str(e)}")
    st.info("Please check your Elasticsearch connection and try again.")
