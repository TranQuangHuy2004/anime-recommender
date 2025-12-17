import streamlit as st
from streamlit_theme import st_theme
from components.anime_card import AnimeCard
from services.database import Database
from services.elasticsearch_service import ElasticsearchService

# Detect current theme
theme = st_theme()

if theme and theme["base"] == "light":
    bg_color = "rgba(200, 200, 200, 0.75)"
    font_color = "rgba(0, 0, 0, 1)"
    border_card = "rgba(0, 0, 0, 0.2)"
    linear_gradient = "linear-gradient(rgba(200, 200, 200, 0.5), rgba(0, 0, 0, 1))"
    button_background = "rgba(255, 255, 255, 0.5)"
    anime_card_background = "rgba(255, 255, 255, 0.5)"
else:
    bg_color = "rgba(0, 0, 0, 0.5)"
    font_color = "rgba(255, 255, 255, 1)"
    border_card = "rgba(255, 255, 255, 0.5)"
    linear_gradient = "linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, .8))"
    button_background = ""
    anime_card_background = "rgba(0, 0, 0, 0)"

st.set_page_config(
    page_title="Anime Recommendation System",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Initialize services with caching
@st.cache_resource
def init_db():
    return Database()


@st.cache_resource
def init_es():
    return ElasticsearchService()


# Store in session state
if 'db' not in st.session_state:
    st.session_state.db = init_db()
if 'es' not in st.session_state:
    st.session_state.es = init_es()

# Get anime ID from session state or query params
if 'selected_anime' not in st.session_state:
    if 'mal_id' not in st.query_params:
        st.error("No anime selected")
        st.stop()
    else:
        anime_id = st.query_params['mal_id']
        st.session_state.selected_anime = anime_id
else:
    anime_id = st.session_state.get('selected_anime')


# Get anime from anime_index
anime = st.session_state.es.get_anime_by_mal_id(anime_id)
image_url = anime.get('image_url')

# Custom CSS
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: {linear_gradient},
                url({image_url});
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

.st-key-title-container [data-testid="stCaptionContainer"] {{
    font-size: 1rem;
    margin-top: 1rem
}}

.st-key-main-content p {{
    font-size: 1.1rem;
}}

.st-key-main-content p strong {{
    margin-right: 0.5rem
}}

.st-key-title-container [data-testid="stMarkdown"] {{
    margin-top: -2rem
}}

.st-key-metadata {{
    margin-bottom: 1rem;
}}

.st-key-synopsis-container [data-testid="stBaseButton-secondary"] {{
    background-color: transparent;
    border: none;
    border-top: 1px solid white
}}

[class*="st-key-va-info-"], [class*="st-key-char-info-"] {{
    gap: 0.4rem
}}

[class*="st-key-va-info-"] div {{
    text-align: right;
}}

[class*="st-key-anime_card_grid"] {{
    padding: 20px 10px;
    overflow-x: auto;
    overflow-y: hidden; 
    white-space: nowrap;
    flex-flow: row;
}}
            
[class*="st-key-anime_card_grid"] > [data-testid="stLayoutWrapper"] {{
    min-width: 200px;
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
    font-size: 0.75rem
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
    font-size: 1.2rem;
}}

[data-testid="stExpander"] summary {{
    background-color: {button_background}
}}

""", unsafe_allow_html=True)


def apply_filters(filters: dict):
    """
    Apply search filters using a dictionary.
    Example:
    {
        "genre": {"mal_id": 1, "name": "Action"},
        "season": "fall",
        "year": 2023
    }
    """
    st.session_state.search_filters = filters
    st.switch_page("pages/2_🔍_Search.py")


# Navigation Buttons
with st.container(horizontal=True):
    if st.button("🏠 Home"):
        st.switch_page("pages/1_🏠_Home.py")
    if st.button("🔍 Search more"):
        st.switch_page("pages/2_🔍_Search.py")

# Display anime details
col1, col2 = st.columns([2, 5], gap="medium")
with col1:
    with st.container(horizontal_alignment="center"):
        if anime.get('image_url'):
            st.image(anime['image_url'], width="stretch")
        if anime.get('trailer_url'):
            st.markdown("**Trailer**")
            st.video(anime['trailer_url'], width="stretch")

with col2:
    with st.container(key="main-content", height="stretch"):
        col_title_1, col_title_2 = st.columns([3, 1])
        with col_title_1:
            with st.container(key="title-container"):
                st.title(anime['title'])
                if anime.get('title_english'):
                    st.caption(anime['title_english'])
        with col_title_2:
            with st.container(horizontal=True, height="stretch", vertical_alignment="center"):
                st.metric(
                    label="Score",
                    value=anime.get("score", "N/A")
                )
                st.metric(
                    label="Popularity",
                    value=f"#{anime.get('popularity')}" if anime.get("popularity") else "N/A"
                )
        st.markdown("---")

        # Metadata
        with st.container(horizontal=True, key="metadata"):
            st.write(f"**Episodes:** {anime.get('episodes', 'N/A')}")
            st.write(f"**Status:** {anime.get('status', 'N/A')}")
            st.write(f"**Aired:** {anime.get('aired_string', 'N/A')}")
            st.write(f"**Duration:** {anime.get('duration', 'N/A')}")
            st.write(f"**Rating:** {anime.get('rating', 'N/A')}")

        # Categories with links
        if anime.get('studios'):
            with st.container():
                st.write("**Studios:**")
                for idx, studio in enumerate(anime['studios']):
                    if st.button(f"🏢 {studio['name']}", key=f"studio_{idx}"):
                        apply_filters({
                            "studio": studio
                        })

        if anime.get('genres'):
            with st.container(key="genre-container"):
                st.write("**Genres:**")
                with st.container(key="genre-list", horizontal=True, width="content"):
                    for idx, genre in enumerate(anime['genres']):
                        if st.button(f"🎭 {genre['name']}", key=f"genre_{idx}"):
                            apply_filters({
                                "genre": genre
                            })

        # Synopsis
        with st.container(key="synopsis-container"):
            st.subheader("Synopsis")
            synopsis = anime.get('synopsis', "No synopsis available.")
            preview_text = synopsis[:600] + "..."
            if len(preview_text) < len(synopsis):
                if "expanded" not in st.session_state:
                    st.session_state.expanded = False
                # Display truncated text
                st.write(preview_text if not st.session_state.expanded else synopsis)
                # Toggle button
                col_1, col_2, col_3 = st.columns([1, 2, 1])
                with col_2:
                    if st.button("⇓" if not st.session_state.expanded else "⇑", width="stretch"):
                        st.session_state.expanded = not st.session_state.expanded
                        st.rerun()
            else:
                st.write(synopsis)

    with st.expander(label="More info"):
        # ── Type ─────────────────────────────
        st.markdown("**Type**")
        if anime.get("type"):
            if st.button(f"📺 {anime['type']}", key="type-btn"):
                apply_filters({
                    "type": anime['type']
                })

        # ── Season + Year ────────────────────
        st.markdown("**Season**")
        if anime.get("season") and anime.get("year"):
            season_label = f"🌸 {anime['season'].title()} {anime['year']}"
            if st.button(season_label, key="season-btn"):
                apply_filters({
                    "season": anime["season"],
                    "year": anime["year"]
                })

        # ── Source ───────────────────────────
        st.markdown("**Source**")
        if anime.get("source"):
            if st.button(f"📚 {anime['source']}", key="source-btn"):
                apply_filters({
                    "source": anime["source"]
                })

        # ── Themes ───────────────────────────
        st.markdown("**Themes**")
        if anime.get("themes"):
            with st.container(horizontal=True):
                for idx, theme in enumerate(anime["themes"]):
                    if st.button(
                        f"✨ {theme['name']}",
                        key=f"theme_{theme['mal_id']}_{idx}"
                    ):
                        apply_filters({
                            "theme": theme
                        })

        # ── Demographics ─────────────────────
        st.markdown("**Demographics**")
        if anime.get("demographics"):
            with st.container(horizontal=True):
                for idx, demo in enumerate(anime["demographics"]):
                    if st.button(
                        f"👥 {demo['name']}",
                        key=f"demo_{demo['mal_id']}_{idx}"
                    ):
                        apply_filters({
                            "demographic": demo
                        })

        # # ── Score & Popularity ───────────────
        # st.markdown("**Metrics**")

        # col_score, col_pop = st.columns(2)

        # with col_score:
        #     st.metric(
        #         label="⭐ Score",
        #         value=anime.get("score", "N/A")
        #     )

        # with col_pop:
        #     st.metric(
        #         label="🔥 Popularity",
        #         value=f"#{anime.get('popularity')}" if anime.get("popularity") else "N/A"
        #     )

# Characters Section
st.markdown("---")
st.subheader("Characters & Voice Actors")

characters = anime['characters']
if characters:
    # Sort characters: Main role first, then by favorites descending
    sorted_characters = sorted(
        characters,
        key=lambda x: (
            # Role sorting: Main = 1, Supporting = 2, others = 3
            1 if x.get('role') == 'Main' else (2 if x.get('role') == 'Supporting' else 3),
            # Then by favorites (descending), handle None values
            -x.get('favorites', 0) if x.get('favorites') is not None else 0
        )
    )

    # Characters container
    cols_chars = st.columns(2)
    for idx, char in enumerate(sorted_characters):
        with cols_chars[idx % 2]:
            # Characters & Voice_actors card
            with st.container(border=True):
                col_char, col_va = st.columns([1, 1])
                with col_char:
                    with st.container(horizontal=True):
                        if char.get('image_url'):
                            st.image(char['image_url'], width=60)
                        with st.container(key=f"char-info-{char['mal_id']}", gap="small"):
                            st.markdown(f"**{char['name']}**")
                            st.caption(f"{char['role']}")
                with col_va:
                    with st.container(horizontal=True, horizontal_alignment="right"):
                        if char.get('voice_actors') and len(char['voice_actors']) > 0:
                            va = char['voice_actors'][0]
                            with st.container(key=f"va-info-{char['mal_id']}-{va['mal_id']}"):
                                st.markdown(f"**{va['name']}**")
                                st.caption("Japanese")
                            if va.get('image_url'):
                                st.image(va['image_url'], width=60)

                        else:
                            st.write("—")


# Similar Anime Section (placeholder for FAISS)
st.markdown("---")
st.header("🎯 Similar Anime")
# Show some anime from same genres
if anime.get('genres') and len(anime['genres']) > 0:
    anime_card = AnimeCard()
    for genre in anime['genres']:
        st.subheader(f"{genre['name']}")
        similar = st.session_state.es.get_genre_anime(genre['name'], size=11)
        if similar and similar.get('hits'):
            with st.container(horizontal=True, key=f"anime_card_grid_{genre['name']}"):
                for idx, sim_anime in enumerate(similar['hits']):
                    if not sim_anime['mal_id'] == anime_id:
                        anime_card.create_anime_card(sim_anime, genre['name'], idx, height=150)

# Navigation Buttons
with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button("🔍 Search more", key="button_search_2"):
        st.switch_page("pages/2_🔍_Search.py")
    if st.button("🏠 Home", key="button_home_2"):
        st.switch_page("pages/1_🏠_Home.py")
