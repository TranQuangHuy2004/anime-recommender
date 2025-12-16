import streamlit as st
from streamlit_card import card


class AnimeCard:
    def __init__(self):
        pass

    def show_anime_details(self, mal_id):
        st.session_state.selected_anime = mal_id
        st.switch_page("pages/4_🎬_Anime_Details.py")

    def create_anime_card(self, anime, keyword, idx,):
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
                        "height": "250px",
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
                st.session_state.selected_anime = anime['mal_id']
                st.switch_page("pages/4_🎬_Anime_Details.py")

            st.caption(f"{anime.get('type', '')} • {anime.get('year', '')}", text_alignment="center")

            # Quick info
            col1, col2 = st.columns(2, vertical_alignment="center")
            with col1:
                st.metric("Score", f"{anime.get('score', 'N/A'):.1f}")
            with col2:
                st.metric("Episodes", anime.get('episodes', 'N/A'))
