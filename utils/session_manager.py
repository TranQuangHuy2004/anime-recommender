import streamlit as st
from typing import Any, Dict, Optional, List
from services.elasticsearch_service import ElasticsearchService
from services.database import Database
import json


@st.cache_resource
def init_db():
    return Database()


@st.cache_resource
def init_es():
    return ElasticsearchService()


class SessionManager:
    """Helper class to manage Streamlit session state with type safety and defaults"""

    def __init__(self):
        """Initialize the session manager"""
        if 'es' not in st.session_state:
            st.session_state.es = init_es()
        if 'db' not in st.session_state:
            st.session_state.db = init_db()
        pass

    # ========== BASIC GET/SET OPERATIONS ==========

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a value in session state"""
        st.session_state[key] = value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a value from session state with optional default"""
        return st.session_state.get(key, default)

    @staticmethod
    def exists(key: str) -> bool:
        """Check if a key exists in session state"""
        return key in st.session_state

    @staticmethod
    def delete(key: str) -> None:
        """Delete a key from session state"""
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def clear_all() -> None:
        """Clear all session state (use with caution!)"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    # ========== TYPE-SAFE OPERATIONS ==========

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get an integer from session state"""
        value = st.session_state.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """Get a float from session state"""
        value = st.session_state.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_str(key: str, default: str = "") -> str:
        """Get a string from session state"""
        value = st.session_state.get(key, default)
        return str(value) if value is not None else default

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get a boolean from session state"""
        value = st.session_state.get(key, default)
        return bool(value)

    @staticmethod
    def get_list(key: str, default: Optional[List] = None) -> List:
        """Get a list from session state"""
        if default is None:
            default = []
        value = st.session_state.get(key, default)
        return list(value) if isinstance(value, (list, tuple)) else default

    @staticmethod
    def get_dict(key: str, default: Optional[Dict] = None) -> Dict:
        """Get a dictionary from session state"""
        if default is None:
            default = {}
        value = st.session_state.get(key, default)
        return dict(value) if isinstance(value, dict) else default

    # ========== SPECIALIZED OPERATIONS ==========

    @staticmethod
    def init(key: str, default: Any) -> Any:
        """
        Initialize a session state key with default value if it doesn't exist.
        Returns the value (either existing or newly set default).
        """
        if key not in st.session_state:
            st.session_state[key] = default
        return st.session_state[key]

    @staticmethod
    def toggle(key: str) -> bool:
        """
        Toggle a boolean value in session state.
        Returns the new value.
        """
        current = st.session_state.get(key, False)
        new_value = not current
        st.session_state[key] = new_value
        return new_value

    @staticmethod
    def increment(key: str, step: int = 1) -> int:
        """
        Increment a numeric value in session state.
        Returns the new value.
        """
        current = SessionManager.get_int(key, 0)
        new_value = current + step
        st.session_state[key] = new_value
        return new_value

    @staticmethod
    def decrement(key: str, step: int = 1) -> int:
        """
        Decrement a numeric value in session state.
        Returns the new value.
        """
        return SessionManager.increment(key, -step)

    @staticmethod
    def append(key: str, value: Any) -> List:
        """
        Append a value to a list in session state.
        Returns the updated list.
        """
        lst = SessionManager.get_list(key, [])
        lst.append(value)
        st.session_state[key] = lst
        return lst

    @staticmethod
    def extend(key: str, values: List) -> List:
        """
        Extend a list in session state with multiple values.
        Returns the updated list.
        """
        lst = SessionManager.get_list(key, [])
        lst.extend(values)
        st.session_state[key] = lst
        return lst

    @staticmethod
    def update_dict(key: str, updates: Dict) -> Dict:
        """
        Update a dictionary in session state.
        Returns the updated dictionary.
        """
        dct = SessionManager.get_dict(key, {})
        dct.update(updates)
        st.session_state[key] = dct
        return dct

    # ========== SEARCH-SPECIFIC HELPERS ==========

    @staticmethod
    def init_search_state() -> None:
        """Initialize all search-related session state variables"""
        defaults = {
            'search_query': '',
            'search_type': 'All',
            'search_filters': {},
            'current_page': 1,
            'sort_by': 'relevance',
            'sort_order': 'desc',
            'filter_type': None,
            'filter_value': None,
            'filter_year': None,
            'selected_anime': None,
            'nav_to_page': None
        }

        for key, default in defaults.items():
            SessionManager.init(key, default)

    @staticmethod
    def reset_search() -> None:
        """Reset search-related session state to defaults"""
        SessionManager.set('search_query', '')
        SessionManager.set('search_type', 'All')
        SessionManager.set('search_filters', {})
        SessionManager.set('current_page', 1)

    @staticmethod
    def get_search_filters() -> Dict:
        """Get search filters with type safety"""
        return SessionManager.get_dict('search_filters', {})

    @staticmethod
    def update_search_filters(updates: Dict) -> Dict:
        """Update search filters and reset to page 1"""
        filters = SessionManager.get_search_filters()
        filters.update(updates)
        SessionManager.set('search_filters', filters)
        SessionManager.set('current_page', 1)  # Reset to first page when filters change
        return filters

    @staticmethod
    def clear_search_filters() -> None:
        """Clear all search filters"""
        SessionManager.set('search_filters', {})
        SessionManager.set('current_page', 1)

    @staticmethod
    def set_filter_by_type(filter_type: str, filter_value: Any, filter_year: Optional[int] = None) -> None:
        """Set filter by type (genre, studio, etc.)"""
        SessionManager.set('filter_type', filter_type)
        SessionManager.set('filter_value', filter_value)
        if filter_year:
            SessionManager.set('filter_year', filter_year)
        SessionManager.set('current_page', 1)

    @staticmethod
    def get_pagination_info() -> Dict:
        """Get pagination information"""
        return {
            'current_page': SessionManager.get_int('current_page', 1),
            'sort_by': SessionManager.get_str('sort_by', '_score'),
            'sort_order': SessionManager.get_str('sort_order', 'desc')
        }

    # ========== ANIME-SPECIFIC HELPERS ==========

    @staticmethod
    def set_selected_anime(mal_id: int) -> None:
        """Set the selected anime for details view"""
        SessionManager.set('selected_anime', mal_id)

    @staticmethod
    def get_selected_anime() -> Optional[int]:
        """Get the selected anime ID"""
        return SessionManager.get('selected_anime')

    @staticmethod
    def clear_selected_anime() -> None:
        """Clear the selected anime"""
        SessionManager.delete('selected_anime')

    # ========== NAVIGATION HELPERS ==========
    @staticmethod
    def navigate_to(page: str) -> None:
        """Navigate to a different page"""
        SessionManager.set('nav_to_page', page)

    @staticmethod
    def should_navigate() -> Optional[str]:
        """Check if navigation is pending and return target page"""
        return SessionManager.get('nav_to_page')

    @staticmethod
    def clear_navigation() -> None:
        """Clear pending navigation"""
        SessionManager.delete('nav_to_page')
