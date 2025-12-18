# pages/3_⚙️_Advanced_Search.py
import streamlit as st
from streamlit_theme import st_theme
from components.search_bar import render_search_bar
from components.random_button import random_anime_button
from utils.session_manager import SessionManager
import utils.helpers as helper

# Clear query params at start
st.query_params.clear()

# Detect current theme
theme = st_theme()

if theme and theme["base"] == "light":
    bg_color = "rgba(200, 200, 200, 0.75)"
    font_color = "rgba(0, 0, 0, 1)"
    border_card = "rgba(0, 0, 0, 0.2)"
    linear_gradient = "linear-gradient(rgba(200, 200, 200, 0.5), rgba(0, 0, 0, 75))"
    button_background = "rgba(255, 255, 255, 0.5)"
    anime_card_background = "rgba(255, 255, 255, 0.5)"
else:
    bg_color = "rgba(0, 0, 0, 0.7)"
    font_color = "rgba(255, 255, 255, 1)"
    border_card = "rgba(255, 255, 255, 0.5)"
    linear_gradient = "linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7))"
    button_background = ""
    anime_card_background = "rgba(0, 0, 0, 0)"

# Page configuration
st.set_page_config(
    page_title="Advanced Search",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Handle navigation
if SessionManager.should_navigate():
    target_page = SessionManager.should_navigate()
    SessionManager.clear_navigation()
    st.switch_page(f"pages/{target_page}")


# Initialize services with caching
SessionManager()
# Initialize session state
SessionManager.init_search_state()
SessionManager.clear_search_filters()

# Custom CSS for better styling
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: {linear_gradient},
                url('https://media.licdn.com/dms/image/v2/C5612AQFLDcNEuFL2fA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1627670644015?e=2147483647&v=beta&t=ygU_Vtd_tAiQrUPdjPkqm1fy2pTZx3grp9Lm4MmH0IY');
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
    max-width: 1200px;
}}

[data-testid="stBaseButton-secondary"] {{
    background-color: {button_background}
    
}}

[data-testid="stExpander"] summary {{
    background-color: {button_background}
}}

[data-testid="stSelectbox"] > div > div {{
    background-color: {button_background}
}}

[data-testid="stExpanderDetails"] {{
    background: {bg_color}
}}

.st-key-random-button  p {{
    font-size: 2rem;
}}

</style>
""", unsafe_allow_html=True)

# Header
with st.container(horizontal=True, vertical_alignment="center"):
    with st.container(horizontal=True):
        if st.button("🏠 Home"):
            SessionManager.navigate_to("1_🏠_Home.py")
            st.rerun()
        if st.button("🔍 Basic Search"):
            SessionManager.navigate_to("2_🔍_Search.py")
            st.rerun()

    random_anime_button()

st.title("⚙️ Advanced Search")
st.markdown("Fine-tune your anime discovery with detailed filters")

render_search_bar(st.session_state.es, advanced=False, stay=True)
st.markdown("---")

# Initialize filter options


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_filter_options():
    return st.session_state.es.get_filter_options(st.session_state.db)


filter_options = get_cached_filter_options()

# Initialize session state for selected filters
if 'advanced_filters' not in st.session_state:
    st.session_state.advanced_filters = {}

# SECTION 1: Basic Filters
st.subheader("Basic Filters")
# with st.container(key="basic-filters"):
col_filter = st.columns(4)

with col_filter[0]:
    # Rating selectbox
    rating_options = ["All"] + filter_options.get('ratings', [])
    selected_rating = st.selectbox(
        "Rating",
        rating_options,
        key="advanced_rating"
    )
    if selected_rating != "All":
        st.session_state.advanced_filters['rating'] = selected_rating

with col_filter[1]:
    # Status selectbox
    status_options = ["All"] + filter_options.get('statuses', [])
    selected_status = st.selectbox(
        "Status",
        status_options,
        key="advanced_status"
    )
    if selected_status != "All":
        st.session_state.advanced_filters['status'] = selected_status

with col_filter[2]:
    # Status selectbox
    source_options = ["All"] + filter_options.get('sources', [])
    selected_source = st.selectbox(
        "Source",
        source_options,
        key="advanced_source"
    )
    if selected_source != "All":
        st.session_state.advanced_filters['source'] = selected_source

with col_filter[3]:
    # Type selectbox
    type_options = ["All"] + filter_options.get('types', [])
    selected_type = st.selectbox(
        "type",
        type_options,
        key="advanced_type"
    )
    if selected_type != "All":
        st.session_state.advanced_filters['type'] = selected_type

col3, col4 = st.columns(2)
with col3:
    # Score slider
    min_score = st.slider(
        "Minimum Score",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        key="advanced_min_score"
    )
    if min_score > 0:
        st.session_state.advanced_filters['min_score'] = min_score

with col4:
    # Year slider
    if 'year_range' in filter_options:
        min_year, max_year = filter_options['year_range']
        year_range = st.slider(
            "Year Range",
            min_year,
            max_year,
            (min_year, max_year),
            key="advanced_year_range"
        )
        if year_range[0] > min_year or year_range[1] < max_year:
            st.session_state.advanced_filters['year_from'] = year_range[0]
            st.session_state.advanced_filters['year_to'] = year_range[1]

st.markdown("---")

# SECTION 2: Category Filters with Counts
st.subheader("Category Filters")


# Function to get counts for each filter item
@st.cache_data(ttl=3600)
def get_filter_counts():
    counts = {}

    # Get total anime count for percentage calculations
    total_query = "SELECT COUNT(*) as total FROM anime"
    result = st.session_state.db.execute_query(total_query)
    total_anime = result[0]['total'] if result else 0

    # Get counts for genres
    genre_counts = st.session_state.db.execute_query("""
        SELECT g.name, COUNT(ag.anime_id) as count
        FROM genres g
        LEFT JOIN anime_genres ag ON g.mal_id = ag.genre_id
        GROUP BY g.name
        ORDER BY g.name
    """)
    counts['genres'] = {g['name']: g['count'] for g in genre_counts} if genre_counts else {}

    # Get counts for themes
    theme_counts = st.session_state.db.execute_query("""
        SELECT t.name, COUNT(at.theme_id) as count
        FROM themes t
        LEFT JOIN anime_themes at ON t.mal_id = at.theme_id
        GROUP BY t.name
        ORDER BY t.name
    """)
    counts['themes'] = {t['name']: t['count'] for t in theme_counts} if theme_counts else {}

    # Get counts for demographics
    demo_counts = st.session_state.db.execute_query("""
        SELECT d.name, COUNT(ad.demographic_id) as count
        FROM demographics d
        LEFT JOIN anime_demographics ad ON d.mal_id = ad.demographic_id
        GROUP BY d.name
        ORDER BY d.name
    """)
    counts['demographics'] = {d['name']: d['count'] for d in demo_counts} if demo_counts else {}

    # Get counts for studios
    studio_counts = st.session_state.db.execute_query("""
        SELECT s.name, COUNT(as2.studio_id) as count
        FROM studios s
        LEFT JOIN anime_studios as2 ON s.mal_id = as2.studio_id
        GROUP BY s.name
        ORDER BY s.name
    """)
    counts['studios'] = {s['name']: s['count'] for s in studio_counts} if studio_counts else {}

    return counts


# Get filter counts
filter_counts = get_filter_counts()
# Create expanders for each category

# Genres expander
with st.expander("🎭 Genres"):
    genres = filter_options.get('genres', [])
    if genres:
        selected_genres = []
        col_genre = st.columns(6)
        for idx, genre in enumerate(genres):
            with col_genre[idx % 6]:
                count = filter_counts.get('genres', {}).get(genre, 0)
                if st.checkbox(f"{genre} ({count})", key=f"genre_{genre}"):
                    selected_genres.append(genre)
        if selected_genres:
            st.session_state.advanced_filters['genres'] = selected_genres
        else:
            st.session_state.advanced_filters.pop('genres', None)

# Themes expander
with st.expander("✨ Themes", expanded=False):
    themes = filter_options.get('themes', [])
    if themes:
        selected_themes = []
        col_theme = st.columns(6)
        for idx, theme in enumerate(themes):
            with col_theme[idx % 6]:
                count = filter_counts.get('themes', {}).get(theme, 0)
                if st.checkbox(f"{theme} ({count})", key=f"theme_{theme}"):
                    selected_themes.append(theme)
        if selected_themes:
            st.session_state.advanced_filters['themes'] = selected_themes
        else:
            st.session_state.advanced_filters.pop('themes', None)

# Demographics expander
with st.expander("👥 Demographics", expanded=False):
    demographics = filter_options.get('demographics', [])
    if demographics:
        selected_demos = []
        col_demo = st.columns(6)
        for idx, demo in enumerate(demographics):
            with col_demo[idx % 6]:
                count = filter_counts.get('demographics', {}).get(demo, 0)
                if st.checkbox(f"{demo} ({count})", key=f"demo_{demo}"):
                    selected_demos.append(demo)
        if selected_demos:
            st.session_state.advanced_filters['demographics'] = selected_demos
        else:
            st.session_state.advanced_filters.pop('demographics', None)

# Studios expander
with st.expander("🏢 Studios"):
    studios = filter_options.get('studios', [])
    if studios:
        selected_studios = []
        col_studio = st.columns(5)
        for idx, studio in enumerate(studios):
            with col_studio[idx % 5]:
                count = filter_counts.get('studios', {}).get(studio, 0)
                if st.checkbox(f"{studio} ({count})", key=f"studio_{studio}"):
                    selected_studios.append(studio)
        if selected_studios:
            st.session_state.advanced_filters['studios'] = selected_studios
        else:
            st.session_state.advanced_filters.pop('studios', None)

st.markdown("---")

# SECTION 3: Season-Year Buttons
st.subheader("Season & Year Quick Filters")

# Get unique season-year combinations


@st.cache_data(ttl=3600)
def get_season_year_combinations():
    query = """
    SELECT season, year, COUNT(*) as anime_count 
    FROM anime 
    WHERE season IS NOT NULL AND year IS NOT NULL
    GROUP BY season, year
    ORDER BY year DESC, 
        CASE season
            WHEN 'winter' THEN 1
            WHEN 'spring' THEN 2
            WHEN 'summer' THEN 3
            WHEN 'fall' THEN 4
            ELSE 5
        END;
    """
    results = st.session_state.db.execute_query(query)
    return results if results else []


season_years = get_season_year_combinations()

if season_years:
    available = {
        (row['season'], row['year']) for row in season_years
    }

    SEASONS = ["winter", "spring", "summer", "fall"]
    years = []
    seen = set()
    for row in season_years:
        year = row['year']
        if year not in seen:
            years.append(year)
            seen.add(year)

    with st.expander("Browse by Season"):
        for year in years:
            st.markdown(f"### {year}")
            cols = st.columns(4)

            for i, season in enumerate(SEASONS):
                with cols[i]:
                    is_available = (season, year) in available
                    if is_available:
                        if st.button(
                            f"{season.title()} {year}",
                            use_container_width=True,
                            disabled=not is_available,
                            key=f"{season}-{year}"
                        ):
                            # Apply season and year filter
                            helper.apply_filters({
                                "season": season,  # Single value
                                "year": year  # Single value
                            }, SessionManager)
                    else:
                        st.button(
                            f"{season.title()} {year}",
                            use_container_width=True,
                            disabled=not is_available,
                            key=f"{season}-{year}"
                        )

    # Show summary
    total_seasons = len(season_years)
    if total_seasons > 0:
        st.caption(f"Showing {total_seasons} season-year combinations")

else:
    st.info("No season data available.")

st.markdown("---")

# Action buttons
if st.button("Apply All Filters & Search", type="primary", use_container_width=True):
    # Apply all selected filters
    SessionManager.update_search_filters(st.session_state.advanced_filters)
    SessionManager.navigate_to("2_🔍_Search.py")
    SessionManager.set('advanced_filters', {})
    st.rerun()


if st.button("🗑️ Clear All Filters", use_container_width=True):
    # Clear all advanced filters
    st.session_state.advanced_filters = {}
    SessionManager.reset_search()
    SessionManager.clear_search_filters()
    st.success("All filters cleared!")
    st.rerun()

# Preview section (always visible when filters are selected)
if st.session_state.advanced_filters:
    st.markdown("---")
    st.subheader("📋 Selected Filters Preview")

    # Display selected filters in a clean format
    filter_cols = st.columns(3)
    filter_items = list(st.session_state.advanced_filters.items())

    for idx, (key, value) in enumerate(filter_items):
        with filter_cols[idx % 3]:
            if isinstance(value, list):
                st.info(f"**{key}:** {', '.join(value[:3])}{'...' if len(value) > 3 else ''}")
            else:
                st.info(f"**{key}:** {value}")
