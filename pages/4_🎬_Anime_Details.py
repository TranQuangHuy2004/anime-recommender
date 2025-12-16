import streamlit as st
from streamlit_theme import st_theme

# Detect current theme
theme = st_theme()

if theme and theme["base"] == "light":
    bg_color = "rgba(200, 200, 200, 0.75)"
    font_color = "rgba(0, 0, 0, 1)"
    border_card = "rgba(0, 0, 0, 0.2)"
    linear_gradient = "linear-gradient(rgba(200, 200, 200, 0.5), rgba(0, 0, 0, 0.7))"
    button_background = "rgba(255, 255, 255, 0.75)"
    anime_card_background = "rgba(255, 255, 255, 0.5)"
else:
    bg_color = "rgba(0, 0, 0, 0.5)"
    font_color = "rgba(255, 255, 255, 1)"
    border_card = "rgba(255, 255, 255, 0.5)"
    linear_gradient = "linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 1))"
    button_background = ""
    anime_card_background = "rgba(0, 0, 0, 0)"

st.set_page_config(
    page_title="Anime Recommendation System",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Get anime ID from session state or query params
anime_id = st.session_state.get('selected_anime')
if not anime_id:
    st.error("No anime selected")
    st.stop()

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
""", unsafe_allow_html=True)

# Display anime details
col1, col2 = st.columns([1, 2])

with col1:
    with st.container(horizontal_alignment="center"):
        if anime.get('image_url'):
            st.image(anime['image_url'], width="content")
        if anime.get('trailer_url'):
            st.markdown("**Trailer**")
            st.video(anime['trailer_url'], width=300)

        # Quick stats
        with st.container(horizontal=True, vertical_alignment="center"):
            st.metric("Score", f"{anime.get('score', 'N/A')}")
            st.metric("Rank", f"#{anime.get('popularity', 'N/A')}")

with col2:
    # Titles
    st.title(anime['title'])
    if anime.get('title_english'):
        st.subheader(anime['title_english'])
    if anime.get('title_japanese'):
        st.write(f"Japanese: {anime['title_japanese']}")

    # Metadata
    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        st.write(f"**Type:** {anime.get('type', 'N/A')}")
    with cols[1]:
        st.write(f"**Episodes:** {anime.get('episodes', 'N/A')}")
    with cols[2]:
        st.write(f"**Status:** {anime.get('status', 'N/A')}")
    with cols[3]:
        st.write(f"**Aired:** {anime.get('aired_string', 'N/A')}")

    # Categories with links
    if anime.get('studios'):
        st.write("**Studios:**")
        cols = st.columns(4)
        for idx, studio in enumerate(anime['studios'][:4]):
            with cols[idx % 4]:
                if st.button(f"🏢 {studio['name']}", key=f"studio_{idx}"):
                    st.session_state.filter_type = "studio"
                    st.session_state.filter_value = studio
                    st.switch_page("pages/2_🔍_Search.py")

    if anime.get('genres'):
        st.write("**Genres:**")
        cols = st.columns(4)
        for idx, genre in enumerate(anime['genres'][:8]):
            with cols[idx % 4]:
                if st.button(f"🎭 {genre['name']}", key=f"genre_{idx}"):
                    st.session_state.filter_type = "genre"
                    st.session_state.filter_value = genre
                    st.switch_page("pages/2_🔍_Search.py")

    # Synopsis
    st.subheader("Synopsis")
    st.write(anime.get('synopsis', 'No synopsis available'))

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
    with st.container(horizontal=True, horizontal_alignment="center"):
        for char in sorted_characters:
            # Characters & Voice_actors card
            with st.container(border=True, width=600):
                col_char, col_va = st.columns([1, 1])
                with col_char:
                    with st.container(horizontal=True):
                        if char.get('image_url'):
                            st.image(char['image_url'], width=60)
                        with st.container():
                            st.markdown(f"**{char['name']}**")
                            st.caption(f"{char['role']}")
                with col_va:
                    with st.container(horizontal=True, horizontal_alignment="right"):
                        if char.get('voice_actors') and len(char['voice_actors']) > 0:
                            va = char['voice_actors'][0]
                            with st.container():
                                st.markdown(f"**{va['name']}**")
                                st.caption("Japanese")
                            if va.get('image_url'):
                                st.image(va['image_url'], width=60)

                        else:
                            st.write("—")


# Similar Anime Section (placeholder for FAISS)
st.markdown("---")
st.subheader("🎯 Similar Anime")
st.info("Similar anime recommendations will be added with FAISS vector search")

# Show some anime from same genres
if anime.get('genres') and len(anime['genres']) > 0:
    similar = st.session_state.es.get_genre_anime(anime['genres'][0], size=6)
    cols = st.columns(6)
    for idx, hit in enumerate(similar[:6]):
        sim_anime = hit['_source']
        if sim_anime['mal_id'] != anime_id:
            with cols[idx]:
                if st.button(f"🎬 {sim_anime['title'][:15]}...", key=f"sim_{idx}"):
                    st.session_state.selected_anime = sim_anime['mal_id']
                    st.rerun()
