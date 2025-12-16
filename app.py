# app.py - Main entry point for Streamlit multipage app
import streamlit as st
from services.database import Database
from services.elasticsearch_service import ElasticsearchService
import time

# Page configuration
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


# Store in session state for access across pages
if 'db' not in st.session_state:
    st.session_state.db = init_db()
if 'es' not in st.session_state:
    st.session_state.es = init_es()

# Simple welcome page that redirects to Home
st.title("🎌 Anime Recommendation System")
st.markdown("""
Welcome to the Anime Recommendation System!
This system uses Elasticsearch and FAISS to provide personalized anime recommendations.

**Navigate using the sidebar menu →**
""")

# Show current page info (Streamlit automatically shows pages in sidebar)
st.sidebar.success("Select a page above")
st.switch_page("pages/1_🏠_Home.py")
