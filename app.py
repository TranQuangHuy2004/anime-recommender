import streamlit as st
from services.database import Database
from services.elasticsearch_service import ElasticsearchService
import pandas as pd
import time

# Page configuration
st.set_page_config(
    page_title="Anime Recommendation System",
    page_icon="🎌",
    layout="wide"
)

# Initialize services with caching


@st.cache_resource
def init_db():
    return Database()


@st.cache_resource
def init_es():
    return ElasticsearchService()


db = init_db()
es = init_es()


# In sidebar section
with st.sidebar:
    st.title("🎌 Anime Recommender")

    # Search box
    search_query = st.text_input("Search anime:", placeholder="Type anime title, character, genre...")

    # Filters
    st.subheader("Filters")

    # Genre filter (get from Elasticsearch)
    genre_query = "SELECT DISTINCT name FROM genres ORDER BY name"
    genres_result = db.execute_query(genre_query)
    all_genres = [g['name'] for g in genres_result] if genres_result else []
    selected_genres = st.multiselect("Genres", all_genres)

    # Type filter
    type_query = "SELECT DISTINCT type FROM anime WHERE type IS NOT NULL ORDER BY type"
    types_result = db.execute_query(type_query)
    all_types = [t['type'] for t in types_result] if types_result else []
    selected_type = st.selectbox("Type", ["All"] + all_types)

    # Score filter
    min_score = st.slider("Minimum Score", 0.0, 10.0, 7.0, 0.5)

    # Year range
    year_query = "SELECT MIN(year) as min_year, MAX(year) as max_year FROM anime WHERE year IS NOT NULL"
    year_result = db.execute_query(year_query)
    if year_result and year_result[0]['min_year']:
        min_year, max_year = year_result[0]['min_year'], year_result[0]['max_year']
        year_range = st.slider("Year Range", min_year, max_year, (min_year, max_year))

    # Season filter
    season_query = "SELECT DISTINCT season FROM anime WHERE season IS NOT NULL ORDER BY season"
    seasons_result = db.execute_query(season_query)
    all_seasons = [s['season'] for s in seasons_result] if seasons_result else []
    selected_season = st.selectbox("Season", ["All"] + all_seasons)


# Main content
st.title("🎌 Anime Search & Recommendation")

# Search with autocomplete suggestions
if search_query and len(search_query) >= 2:
    # Show autocomplete suggestions
    suggestions = es.autocomplete(search_query)
    if suggestions:
        st.caption(f"Suggestions: {', '.join([s['text'] for s in suggestions[:3]])}")

# Build Elasticsearch query
filters = {}
if selected_genres:
    filters['genres'] = selected_genres
if selected_type != "All":
    filters['type'] = selected_type
if min_score > 0:
    filters['min_score'] = min_score
if 'year_range' in locals():
    filters['year_from'], filters['year_to'] = year_range
if selected_season != "All":
    filters['season'] = selected_season

# Perform search
if search_query or filters:
    results = es.search_anime(search_query, filters=filters, size=50)

    if results:
        st.success(f"Found {len(results)} anime")

        # Display results
        cols = st.columns(3)
        for idx, hit in enumerate(results):
            anime = hit['_source']
            with cols[idx % 3]:
                with st.container(border=True):
                    # Display image if available
                    if anime.get('image_url'):
                        st.image(anime['image_url'], width=200)

                    st.markdown(f"### {anime['title']}")

                    if anime.get('title_english'):
                        st.caption(f"English: {anime['title_english']}")

                    # Quick info
                    col1, col2 = st.columns(2)
                    with col1:
                        if anime.get('score'):
                            st.metric("Score", f"{anime['score']:.2f}")
                    with col2:
                        if anime.get('episodes'):
                            st.metric("Episodes", anime['episodes'])

                    # Tags
                    if anime.get('type'):
                        st.write(f"**Type:** {anime['type']}")
                    if anime.get('genres') and len(anime['genres']) > 0:
                        genre_tags = ", ".join([g['name'] for g in anime['genres'][:3]])
                        st.write(f"**Genres:** {genre_tags}")

                    # View details button
                    if st.button("View Details", key=f"view_{anime['mal_id']}", type="secondary"):
                        st.session_state.selected_anime = anime['mal_id']
    else:
        st.info("No anime found. Try different search terms or filters.")
else:
    # Default view - show popular anime
    st.info("👆 Start typing to search anime, or use filters above")

    # Show some popular anime by default
    default_results = es.search_across_all("", size=9)
    if default_results:
        st.subheader("Popular Anime")
        cols = st.columns(3)
        for idx, hit in enumerate(default_results[:9]):
            anime = hit['_source']
            with cols[idx % 3]:
                with st.container(border=True):
                    if anime.get('image_url'):
                        st.image(anime['image_url'], width=150)
                    st.write(f"**{anime['title']}**")
                    if anime.get('score'):
                        st.write(f"⭐ {anime['score']:.1f}")


# Anime detail view
if 'selected_anime' in st.session_state:
    st.markdown("---")
    st.subheader("Anime Details")

    # Get full details from PostgreSQL (not Elasticsearch)
    mal_id = st.session_state.selected_anime
    anime_query = """
    SELECT * FROM anime WHERE mal_id = %s
    """
    anime_result = db.execute_query(anime_query, (mal_id,))

    if anime_result and len(anime_result) > 0:
        anime = anime_result[0]

        col1, col2 = st.columns([1, 2])

        with col1:
            if anime.get('image_url'):
                st.image(anime['image_url'], width=300)

        with col2:
            st.markdown(f"# {anime['title']}")
            if anime.get('title_english'):
                st.markdown(f"### {anime['title_english']}")
            if anime.get('title_japanese'):
                st.write(f"Japanese: {anime['title_japanese']}")

            # Stats row
            cols_stats = st.columns(4)
            with cols_stats[0]:
                if anime.get('score'):
                    st.metric("Score", f"{anime['score']:.2f}")
            with cols_stats[1]:
                if anime.get('episodes'):
                    st.metric("Episodes", anime['episodes'])
            with cols_stats[2]:
                if anime.get('type'):
                    st.metric("Type", anime['type'])
            with cols_stats[3]:
                if anime.get('year'):
                    st.metric("Year", anime['year'])

            # Synopsis
            if anime.get('synopsis'):
                with st.expander("Synopsis", expanded=True):
                    st.write(anime['synopsis'])

            # Get related data
            # Studios
            studios_query = """
            SELECT s.name FROM studios s
            JOIN anime_studios ast ON s.mal_id = ast.studio_id
            WHERE ast.anime_id = %s
            """
            studios = db.execute_query(studios_query, (mal_id,))
            if studios:
                st.write(f"**Studios:** {', '.join([s['name'] for s in studios])}")

            # Genres
            genres_query = """
            SELECT g.name FROM genres g
            JOIN anime_genres ag ON g.mal_id = ag.genre_id
            WHERE ag.anime_id = %s
            """
            genres = db.execute_query(genres_query, (mal_id,))
            if genres:
                st.write(f"**Genres:** {', '.join([g['name'] for g in genres])}")

        # Show similar anime recommendations
        st.markdown("---")
        st.subheader("Similar Anime")
        similar_anime = es.get_genre_anime(genres[0]['name'] if genres else "", size=6)
        if similar_anime:
            cols = st.columns(6)
            for idx, hit in enumerate(similar_anime[:6]):
                similar = hit['_source']
                if similar['mal_id'] != mal_id:  # Don't show the same anime
                    with cols[idx]:
                        if similar.get('image_url'):
                            st.image(similar['image_url'], width=100)
                        st.write(f"**{similar['title'][:15]}...**" if len(similar['title']) > 15 else f"**{similar['title']}**")
                        if similar.get('score'):
                            st.write(f"⭐ {similar['score']:.1f}")

# Footer with stats
st.markdown("---")
col1, col2, col3 = st.columns(3)

# Get stats from Elasticsearch
try:
    stats = es.es.indices.stats(index=es.indices['anime'])
    anime_count = stats['_all']['total']['docs']['count']

    with col1:
        st.metric("Total Anime", anime_count)
    with col2:
        st.metric("Search Index Size", f"{stats['_all']['total']['store']['size_in_bytes'] / (1024 * 1024):.1f} MB")
    with col3:
        # Get average score
        avg_score_query = "SELECT ROUND(AVG(score)::numeric, 2) as avg_score FROM anime WHERE score IS NOT NULL"
        avg_result = db.execute_query(avg_score_query)
        if avg_result and avg_result[0]['avg_score']:
            st.metric("Average Score", f"{avg_result[0]['avg_score']:.2f}")
except:
    pass
