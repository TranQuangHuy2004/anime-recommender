from datetime import datetime
import re
import streamlit as st


def extract_year_month_season(date_str):
    """
    Extract the first (year, month) from a date string
    and return the corresponding season.
    """

    match = re.search(r'([A-Za-z]{3})\s+\d{1,2},\s*(\d{4})', date_str)
    if not match:
        return None

    month_str, year = match.groups()
    month = datetime.strptime(month_str, "%b").month

    season = get_season(month)

    return int(year), season


def get_season(month):
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"


def apply_filters(filters: dict, SessionManager):
    """
    Apply search filters using a dictionary.
    The filters should match what elasticsearch_service.search_anime() expects.
    """
    SessionManager.set('search_query', '')
    SessionManager.set('search_type', 'All')
    SessionManager.set('search_filters', filters)
    SessionManager.set('sort_order', 'desc')
    SessionManager.set('sort_by', 'relevance')
    SessionManager.set('current_page', 1)

    st.switch_page("pages/6_🎭_Single_Filter_Page.py")
