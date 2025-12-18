import streamlit as st
from components.anime_card import AnimeCard
from streamlit_theme import st_theme
from components.search_bar import render_search_bar
from components.random_button import random_anime_button
import utils.helpers as helper
from utils.session_manager import SessionManager

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
    bg_color = "rgba(0, 0, 0, 0.75)"
    font_color = "rgba(255, 255, 255, 1)"
    border_card = "rgba(255, 255, 255, 0.5)"
    linear_gradient = "linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, .8))"
    button_background = "rgb(19, 23, 32, 0.5)"
    anime_card_background = "rgba(0, 0, 0, 0)"

# Page configuration
st.set_page_config(
    page_title="Anime Recommendation System",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Initialize services
SessionManager()

# Custom CSS
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: {linear_gradient},
                url('https://images3.alphacoders.com/948/thumb-1920-948700.jpg');
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
    max-width: 1400px;
}}
            
[class*="st-key-anime_card_grid"] {{
    padding: 20px 10px;
    overflow-x: auto;
    overflow-y: hidden; 
    white-space: nowrap;
    flex-flow: row;
}}
            
[class*="st-key-anime_card_grid"] > [data-testid="stLayoutWrapper"] {{
    min-width: 245px;
}}
            
[class*="st-key-individual_anime_card_"] {{
    border: 3px solid {border_card};
    background-color: {anime_card_background}
}}
            
[class*="st-key-individual_anime_card_"]:hover {{
    transition: transform 0.5s ease;
    transform: scale(1.05);
}}

[class*="st-key-individual_anime_card_"] button {{
    background-color: {button_background}
}}

[data-testid="stBaseButton-secondary"] {{
    background-color: {button_background}
}}
            
[class*="st-key-individual_anime_card_"] [data-testid="stBaseButton-secondary"] div[data-testid="stMarkdownContainer"] p {{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
    width: 100%;
}}
            
[class*="st-key-individual_anime_card_"] [data-testid="stBaseButton-secondary"] span {{
    overflow: hidden;
    width: 100%;
}}

[class*="st-key-individual_anime_card_"] [data-testid="stCaptionContainer"]{{
    margin-bottom: -1.75rem;
}}
            
[data-testid="stMetric"] {{
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}}
            
[data-testid="stMetricValue"] {{
    font-size: 1.5rem;
}}

.st-key-random-button  p {{
    font-size: 2rem;
}}

</style>
""", unsafe_allow_html=True)


# Main content
with st.container():
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container():
            st.title("🎌 Anime Recommender")
            st.markdown("##### Discover your next favorite anime")
        random_anime_button()

    st.markdown("#### Search Anime")

    # Search bar layout
    render_search_bar(st.session_state.es)

    st.markdown("---")
    anime_card = AnimeCard()
    # Popular Anime
    st.subheader("🔥 Popular Anime")
    try:
        popular_results = st.session_state.es.search_anime("", size=15)
        if popular_results and popular_results.get('hits'):
            with st.container(horizontal=True, key="anime_card_grid_popular"):
                for idx, anime in enumerate(popular_results['hits'][:15]):
                    anime_card.create_anime_card(anime, "pop", idx)

            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                if st.button(f"View All Popular Anime →", key=f"view_all_pop", use_container_width=True):
                    helper.apply_filters({}, SessionManager)
        else:
            st.info("No popular anime found.")
    except Exception as e:
        st.error(f"Error loading popular anime: {str(e)}")

    st.markdown("---")

    # Genre/Movie sections
    sections = [
        ("Slice of Life", "genre"),
        ("Sci-Fi", "genre"),
        ("Horror", "genre"),
        ("Comedy", "genre"),
        ("Movie", "type")
    ]

    for name, filter_type in sections:
        try:
            if filter_type == "type":
                st.subheader("🎥 Movies")
                results = st.session_state.es.search_anime("", filters={"type": "Movie"}, size=10)
            else:
                st.subheader(f"{name} Anime")
                results = st.session_state.es.search_anime("", filters={"genres": [name]}, size=10)

            if results and results.get('hits'):
                with st.container(horizontal=True, key=f"anime_card_grid_{name.lower()}"):
                    for idx, anime in enumerate(results['hits'][:10]):
                        anime_card.create_anime_card(anime, name.lower(), idx)

                # View all button
                col1, col2, col3 = st.columns([1, 3, 1])
                with col2:
                    if st.button(f"View All {name} →", key=f"view_all_{name}", use_container_width=True):
                        if filter_type == "type":
                            helper.apply_filters({
                                "type": name
                            }, SessionManager)
                        else:
                            helper.apply_filters({
                                "genres": [name]  # Must be a list
                            }, SessionManager)
            else:
                st.info(f"No {name.lower()} anime found.")
        except Exception as e:
            st.error(f"Error loading {name} anime: {str(e)}")

        st.markdown("---")

    # Footer
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**🎌 Anime Recommendation System**")
        st.caption("Built with Elasticsearch + Streamlit")

    with col2:
        try:
            stats = st.session_state.db.execute_query("SELECT COUNT(*) as total FROM anime")
            if stats:
                st.metric("Total Anime", f"{stats[0]['total']:,}")
        except:
            st.write("**Database:** Connected")

    with col3:
        try:
            if st.session_state.es.es.ping():
                st.success("✅ Elasticsearch: Online")
            else:
                st.error("❌ Elasticsearch: Offline")
        except:
            st.error("❌ Elasticsearch: Connection failed")
