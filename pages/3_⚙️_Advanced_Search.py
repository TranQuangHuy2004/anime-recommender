# pages/3_⚙️_Advanced_Search.py
import streamlit as st

st.set_page_config(page_title="Advanced Search", layout="wide")

st.title("⚙️ Advanced Search")

# Main search bar
col1, col2 = st.columns([4, 1])
with col1:
    search_query = st.text_input("", placeholder="Search...", label_visibility="collapsed")
with col2:
    if st.button("🔍 Search", use_container_width=True):
        st.session_state.search_query = search_query
        st.switch_page("pages/2_🔍_Search.py")

st.markdown("---")

# Get filter options from database
db = st.session_state.db

# Genre Section
st.subheader("🎭 Genres")
genre_query = """
SELECT g.name, COUNT(DISTINCT a.mal_id) as anime_count 
FROM genres g
LEFT JOIN anime_genres ag ON g.mal_id = ag.genre_id
LEFT JOIN anime a ON ag.anime_id = a.mal_id
GROUP BY g.name
ORDER BY anime_count DESC
"""
genres = db.execute_query(genre_query)

cols = st.columns(4)
for idx, genre in enumerate(genres):
    with cols[idx % 4]:
        if st.button(f"{genre['name']} ({genre['anime_count']})", use_container_width=True):
            st.session_state.filter_type = "genre"
            st.session_state.filter_value = genre['name']
            st.switch_page("pages/2_🔍_Search.py")

st.markdown("---")

# Studio Section
st.subheader("🏢 Studios")
studio_query = """
SELECT s.name, COUNT(DISTINCT a.mal_id) as anime_count 
FROM studios s
LEFT JOIN anime_studios ast ON s.mal_id = ast.studio_id
LEFT JOIN anime a ON ast.anime_id = a.mal_id
GROUP BY s.name
ORDER BY anime_count DESC
LIMIT 20
"""
studios = db.execute_query(studio_query)

cols = st.columns(4)
for idx, studio in enumerate(studios):
    with cols[idx % 4]:
        if st.button(f"{studio['name']} ({studio['anime_count']})", use_container_width=True):
            st.session_state.filter_type = "studio"
            st.session_state.filter_value = studio['name']
            st.switch_page("pages/2_🔍_Search.py")

st.markdown("---")

# Type Section
st.subheader("📺 Type")
type_query = """
SELECT type, COUNT(*) as anime_count 
FROM anime 
WHERE type IS NOT NULL
GROUP BY type
ORDER BY anime_count DESC
"""
types = db.execute_query(type_query)

cols = st.columns(5)
for idx, type_item in enumerate(types):
    with cols[idx % 5]:
        if st.button(f"{type_item['type']} ({type_item['anime_count']})", use_container_width=True):
            st.session_state.filter_type = "type"
            st.session_state.filter_value = type_item['type']
            st.switch_page("pages/2_🔍_Search.py")

st.markdown("---")

# Season + Year Section
st.subheader("🌸 Season & Year")
season_year_query = """
SELECT season, year, COUNT(*) as anime_count 
FROM anime 
WHERE season IS NOT NULL AND year IS NOT NULL
GROUP BY season, year
ORDER BY year DESC, 
    CASE season
        WHEN 'Winter' THEN 1
        WHEN 'Spring' THEN 2
        WHEN 'Summer' THEN 3
        WHEN 'Fall' THEN 4
        ELSE 5
    END
LIMIT 20
"""
seasons = db.execute_query(season_year_query)

cols = st.columns(4)
for idx, season in enumerate(seasons):
    with cols[idx % 4]:
        if st.button(f"{season['season']} {season['year']} ({season['anime_count']})", use_container_width=True):
            st.session_state.search_filters = {
                'season': season['season'],
                'year_from': season['year'],
                'year_to': season['year']
            }
            st.switch_page("pages/2_🔍_Search.py")
