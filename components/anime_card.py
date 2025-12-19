import streamlit as st
from streamlit_card import card
from utils.session_manager import SessionManager


class AnimeCard:
    def __init__(self):
        pass

    def show_anime_details(self, mal_id):
        SessionManager.set('selected_anime', mal_id)
        SessionManager.set('search_query', '')
        SessionManager.set('search_type', 'All')
        SessionManager.set('search_filters', {})
        SessionManager.set('sort_order', 'desc')
        SessionManager.set('sort_by', 'relevence')
        SessionManager.set('current_page', 1)
        SessionManager.delete('random_themes')
        query = {
            'mal_id': f"{mal_id}"
        }
        st.switch_page("pages/4_🎬_Anime_Details.py", query_params=query)

    def create_anime_card(self, anime, keyword, idx, height=250):
        """Generates a single anime card."""
        # Create a card container
        with st.container(border=True, key=f"individual_anime_card_{keyword}_{idx}"):
            # Image
            card(
                title="",
                text="",
                image=anime.get('image_url'),
                styles={
                    "card": {
                        "padding": "0",
                        "margin": "0",
                        "width": "100%",
                        "height": f"{height}px",
                        "border-radius": "0",
                    },
                    "filter": {
                        "background-color": "rgba(0, 0, 0, 0)"
                    }
                },
                key=f"image_{keyword}_{anime['mal_id']}",
                on_click=lambda mal_id=anime['mal_id']: self.show_anime_details(mal_id),
            )

            # Title with click
            if st.button(
                f"**{anime['title']}**",
                key=f"{keyword}_{anime['mal_id']}",
                use_container_width=True,
                help=f"{anime['title']}"
            ):
                SessionManager.set('selected_anime', anime['mal_id'])
                SessionManager.set('search_query', '')
                SessionManager.set('search_type', 'All')
                SessionManager.set('search_filters', {})
                SessionManager.set('sort_order', 'desc')
                SessionManager.set('sort_by', 'relevence')
                SessionManager.set('current_page', 1)
                SessionManager.delete('random_themes')
                query = {
                    'mal_id': f"{anime['mal_id']}"
                }
                st.switch_page("pages/4_🎬_Anime_Details.py", query_params=query)

            st.caption(f"{anime.get('type', '')} • {anime.get('year', '')}", text_alignment="center")

            # Quick info
            col1, col2 = st.columns(2, vertical_alignment="center")
            with col1:
                st.metric("Score", f"{anime.get('score', 'N/A'):.1f}")
            with col2:
                st.metric("Episodes", anime.get('episodes', 'N/A'))

    def create_anime_card_1(self, anime, keyword=None, idx=None):
        with st.container(horizontal=True, vertical_alignment="center", key=f"individual_anime_card_{keyword}_{idx}", gap="medium"):
            if anime.get('image_url'):
                st.image(anime['image_url'], width=200)

            # Content on the right
            with st.container():
                # Title and metadata
                st.markdown(f"### {anime['title']}")

                if anime.get('title_english'):
                    st.caption(f"English: {anime['title_english']}")

                # Quick stats in a row
                col_stats1, col_stats2, col_stats3, col_stats4, col_stats5 = st.columns(5)
                with col_stats1:
                    st.metric("Score", f"{anime.get('score', 'N/A')}")
                with col_stats2:
                    st.metric("Year", anime.get('year', 'N/A'))
                with col_stats3:
                    st.metric("Episodes", anime.get('episodes', 'N/A'))
                with col_stats4:
                    popularity = anime.get('popularity', 'N/A')
                    st.metric("Popularity", f"#{popularity}" if popularity != 'N/A' else popularity)
                with col_stats5:
                    st.metric("Type", anime.get('type', 'N/A'))

                # Synopsis preview
                if anime.get('synopsis'):
                    synopsis = anime['synopsis']
                    preview = synopsis[:200] + "..." if len(synopsis) > 200 else synopsis
                    st.write(preview)

                # Genres
                if anime.get('genre_names'):
                    genres = anime['genre_names']  # Show first 5 genres
                    genre_text = " | ".join(genres)
                    st.caption(f"**Genres:** {genre_text}")

                if st.button("View Details", key=f"view_{anime['mal_id']}", use_container_width=True):
                    st.session_state.selected_anime = anime['mal_id']
                    query = {
                        'mal_id': f"{anime['mal_id']}"
                    }
                    st.switch_page("pages/4_🎬_Anime_Details.py", query_params=query)
