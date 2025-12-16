# pages/2_🔍_Search.py
import streamlit as st

st.set_page_config(page_title="Search Results", layout="wide")

# Header
st.title("🔍 Search Results")

# Get search parameters
search_query = st.session_state.get('search_query', '')
search_type = st.session_state.get('search_type', 'All')
filter_type = st.session_state.get('filter_type')
filter_value = st.session_state.get('filter_value')

# Show what we're searching for
if search_query:
    st.write(f"**Searching for:** '{search_query}' in **{search_type}**")
elif filter_type and filter_value:
    st.write(f"**Browsing:** {filter_value} {filter_type}")

# Search bar at top
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    new_search = st.text_input("", value=search_query, placeholder="Search anime...", label_visibility="collapsed")
with col2:
    new_type = st.selectbox("Category", ["All", "Anime", "Studio", "Genre", "Character"],
                            index=["All", "Anime", "Studio", "Genre", "Character"].index(search_type) if search_type in ["All", "Anime", "Studio", "Genre", "Character"] else 0,
                            label_visibility="collapsed")
with col3:
    if st.button("🔍 Search", use_container_width=True):
        st.session_state.search_query = new_search
        st.session_state.search_type = new_type
        st.rerun()

# Sort options
col1, col2, col3 = st.columns(3)
with col1:
    sort_by = st.selectbox("Sort by", ["Relevance", "Score", "Popularity", "Year", "Episodes"])
with col2:
    sort_order = st.selectbox("Order", ["Descending", "Ascending"])
with col3:
    results_per_page = st.selectbox("Results per page", [20, 50, 100])

# Perform search
if filter_type and filter_value:
    # Filter search
    filters = {}
    if filter_type == "genre":
        filters['genres'] = [filter_value]
    elif filter_type == "type":
        filters['type'] = filter_value
    elif filter_type == "studio":
        filters['studios'] = [filter_value]

    search_results = st.session_state.es.search_anime("", filters=filters, size=results_per_page)
else:
    # Regular search
    search_results = st.session_state.es.search_anime(search_query, size=results_per_page)

# Display results
st.write(f"**Found {search_results['total']} results**")

# Pagination
if search_results['total_pages'] > 1:
    page_numbers = []
    current_page = search_results.get('page', 1)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col3:
        page_input = st.number_input("Page", min_value=1, max_value=search_results['total_pages'], value=current_page)
        if page_input != current_page:
            # Re-search with new page
            pass

# Display anime cards (3 per row)
animes = search_results['hits']
for i in range(0, len(animes), 3):
    cols = st.columns(3)
    row_animes = animes[i:i+3]

    for idx, hit in enumerate(row_animes):
        anime = hit['_source']
        with cols[idx]:
            with st.container(border=True):
                # Image
                if anime.get('image_url'):
                    st.image(anime['image_url'], use_column_width=True)

                # Title
                st.markdown(f"### {anime['title']}")
                if anime.get('title_english'):
                    st.caption(f"English: {anime['title_english']}")

                # Quick info
                info_cols = st.columns(3)
                with info_cols[0]:
                    st.metric("Score", f"{anime.get('score', 'N/A')}")
                with info_cols[1]:
                    st.metric("Episodes", anime.get('episodes', 'N/A'))
                with info_cols[2]:
                    st.metric("Year", anime.get('year', 'N/A'))

                # Synopsis preview
                if anime.get('synopsis'):
                    synopsis = anime['synopsis'][:150] + "..." if len(anime['synopsis']) > 150 else anime['synopsis']
                    with st.expander("Synopsis"):
                        st.write(synopsis)

                # View details button
                if st.button("View Details", key=f"view_{anime['mal_id']}", use_container_width=True):
                    st.session_state.selected_anime = anime['mal_id']
                    st.switch_page("pages/4_🎬_Anime_Details.py")
