import streamlit as st
from services.database import Database
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Anime Recommender",
    page_icon="🎌",
    layout="wide"
)


# Initialize database
@st.cache_resource
def init_db():
    return Database()


db = init_db()

# Sidebar
with st.sidebar:
    st.title("🎌 Anime Recommender")
    st.markdown("""
    This is a simple anime recommendation system.
    
    **Features:**
    - Search anime
    - Filter by score
    - View details
    """)

    # Filters
    st.subheader("Filters")
    min_score = st.slider("Minimum Score", 0.0, 10.0, 0.0, 0.5)
    show_type = st.selectbox("Type", ["All", "TV", "Movie", "OVA", "Special"])

# Main content
st.title("Anime Database Explorer")

# Search
search_query = st.text_input("Search anime by title:", placeholder="Enter anime title...")

# Build query
query = "SELECT * FROM anime WHERE score >= %s"
params = [min_score]

if search_query:
    query += " AND (title ILIKE %s OR title_english ILIKE %s)"
    params.extend([f"%{search_query}%", f"%{search_query}%"])

if show_type != "All":
    query += " AND type = %s"
    params.append(show_type)

query += " ORDER BY score DESC LIMIT 50"

# Execute query
try:
    results = db.execute_query(query, tuple(params))

    if results:
        # Convert to DataFrame for display
        df = pd.DataFrame(results)

        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Anime", len(results))
        with col2:
            avg_score = df['score'].mean()
            st.metric("Average Score", f"{avg_score:.2f}")
        with col3:
            st.metric("Total Members", f"{df['members'].sum():,}")

        # Display anime cards
        st.subheader("Anime List")

        cols = st.columns(3)
        for idx, anime in enumerate(results):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {anime['title']}")
                    if anime['title_english']:
                        st.caption(f"English: {anime['title_english']}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Score", anime['score'])
                    with col_b:
                        st.metric("Episodes", anime['episodes'] or "N/A")

                    st.write(f"**Type:** {anime['type']}")

                    if anime['synopsis']:
                        with st.expander("Synopsis"):
                            st.write(anime['synopsis'])
    else:
        st.info("No anime found. Try different filters.")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure you've fetched anime data first!")

# Footer
st.markdown("---")
st.markdown("""
**Next Steps:**
1. Run `python scripts/fetch_anime.py` to get data
2. Add Elasticsearch for better search
3. Add FAISS for recommendations
""")
