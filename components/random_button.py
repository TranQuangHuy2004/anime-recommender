import streamlit as st
import random
from utils.session_manager import SessionManager


def random_anime_button(label="🎲"):
    """Super simple random anime button"""

    if st.button(label, width="content", help="Press this! If you don't know what to search :)", key="random-button"):
        try:
            # Get total count from Elasticsearch
            es = st.session_state.es
            count_response = es.es.count(index=es.indices['anime'])
            total_anime = count_response['count']

            if total_anime == 0:
                st.error("No anime in database")
                return

            # Pick random offset
            random_offset = random.randint(0, total_anime - 1)
            # Get anime at random offset
            query = {
                "query": {"match_all": {}},
                "size": 1,
                "from": random_offset
            }

            response = es.es.search(
                index=es.indices['anime'],
                body=query
            )

            if response['hits']['hits']:
                anime = response['hits']['hits'][0]['_source']
                SessionManager.set_selected_anime(anime['mal_id'])
                query = {
                    'mal_id': f"{anime['mal_id']}"
                }
                st.switch_page("pages/4_🎬_Anime_Details.py", query_params=query)
            else:
                st.error("Could not get random anime")

        except Exception as e:
            st.error(f"Error: {str(e)}")
