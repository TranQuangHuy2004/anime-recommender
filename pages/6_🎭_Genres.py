# pages/6_🎭_Genres.py
import streamlit as st

st.set_page_config(page_title="Genres", layout="wide")

st.title("🎭 Genres")

# Get all genres with counts
db = st.session_state.db
query = """
SELECT g.name, COUNT(DISTINCT a.mal_id) as anime_count 
FROM genres g
LEFT JOIN anime_genres ag ON g.mal_id = ag.genre_id
LEFT JOIN anime a ON ag.anime_id = a.mal_id
GROUP BY g.name
ORDER BY g.name
"""
genres = db.execute_query(query)

# Display as grid
cols_per_row = 4
for i in range(0, len(genres), cols_per_row):
    cols = st.columns(cols_per_row)
    row_genres = genres[i:i+cols_per_row]

    for idx, genre in enumerate(row_genres):
        with cols[idx]:
            # Genre card
            with st.container(border=True):
                st.markdown(f"### {genre['name']}")
                st.write(f"**{genre['anime_count']} anime**")

                if st.button("Browse Anime", key=f"browse_{genre['name']}", use_container_width=True):
                    st.session_state.filter_type = "genre"
                    st.session_state.filter_value = genre['name']
                    st.switch_page("pages/2_🔍_Search.py")
