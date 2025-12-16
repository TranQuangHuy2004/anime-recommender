# test_elasticsearch_indices.py
# A simple standalone script to test your Elasticsearch indices
# Run this after your data has been indexed (no re-indexing here)
# It will:
# - Connect via your ElasticsearchService
# - Refresh indices
# - Show document counts
# - Test fetching a specific anime by MAL ID
# - Test filtering anime by genre/studio/etc.
# - Test the completion suggester (autocomplete) with correct context name ("entity_type")
# - Test fuzzy/prefix suggestions

from services.elasticsearch_service import ElasticsearchService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_suggest(es_service, prefix, entity_types=None, size=10):
    """Test the completion suggester with the correct context name ('entity_type')"""
    body = {
        "suggest": {
            "suggestions": {
                "prefix": prefix,
                "completion": {
                    "field": "suggest",
                    "size": size,
                    "fuzzy": {
                        "fuzziness": "AUTO"
                    }
                }
            }
        }
    }

    if entity_types is None:  # unfiltered
        context_values = ["global"]
    else:
        context_values = entity_types if isinstance(entity_types, list) else [entity_types]

    body["suggest"]["suggestions"]["completion"]["contexts"] = {
        "entity_type": context_values
    }

    try:
        response = es_service.es.search(
            index=es_service.indices['search_suggestions'],
            body=body
        )
        options = response['suggest']['suggestions'][0]['options']
        print(f"\nSuggestions for prefix '{prefix}'"
              + (f" (filtered to {entity_types})" if entity_types else " (all types)"))
        print("-" * 60)
        if not options:
            print("No suggestions found")
            return

        for opt in options:
            src = opt['_source']
            print(f"{src.get('name', 'N/A'):40} | type: {src.get('type')} "
                  f"| subtype: {src.get('subtype', 'N/A')} "
                  f"| score: {opt['_score']:.2f}")
        print()
    except Exception as e:
        logger.error(f"Suggest error for '{prefix}': {e}")


if __name__ == "__main__":
    es_service = ElasticsearchService()

    # Force refresh so counts are up-to-date
    for index_name in es_service.indices.values():
        try:
            es_service.es.indices.refresh(index=index_name)
        except Exception as e:
            logger.warning(f"Could not refresh {index_name}: {e}")

    # Document counts
    print("\n" + "="*60)
    print("INDEX DOCUMENT COUNTS")
    print("="*60)
    for logical_name, index_name in es_service.indices.items():
        try:
            count = es_service.es.count(index=index_name)['count']
            print(f"{logical_name:20} -> {index_name:30} | {count:,} documents")
        except Exception as e:
            print(f"{logical_name:20} -> {index_name:30} | Error: {e}")

    # Test fetching specific anime by MAL ID
    print("\n" + "="*60)
    print("FETCH ANIME BY MAL ID")
    print("="*60)
    test_ids = [
        (20, "Naruto"),
        (21, "One Piece"),
        (5114, "Fullmetal Alchemist: Brotherhood"),
        (16498, "Attack on Titan"),
    ]
    for mal_id, expected_title in test_ids:
        doc = es_service.get_anime_by_mal_id(mal_id)
        if doc:
            print(f"MAL {mal_id}: {doc.get('title')}/{doc.get('title_english')}/{doc.get('title_japanese')} (popularity: {doc.get('popularity')})")
        else:
            print(f"MAL {mal_id}: Not found or error")

    # Test filtering anime
    print("\n" + "="*60)
    print("FILTER TESTS (top 5 results)")
    print("="*60)

    for filter_name, func, arg in [
        ("Genre 'Action'", es_service.get_genre_anime, "Action"),
        ("Genre 'Comedy'", es_service.get_genre_anime, "Comedy"),
        ("Studio 'Madhouse'", es_service.get_studio_anime, "Madhouse"),
        ("Theme 'School'", es_service.get_theme_anime, "School"),
        ("Demographic 'Shounen'", es_service.get_demographic_anime, "Shounen"),
    ]:
        try:
            hits = func(arg, size=5)
            titles = [hit['_source']['title'] for hit in hits]
            print(f"{filter_name}: {titles or 'None'}")
        except Exception as e:
            print(f"{filter_name}: Error - {e}")

    # Test autocomplete / completion suggester
    print("\n" + "="*60)
    print("AUTOCOMPLETE / SUGGESTION TESTS")
    print("="*60)

    test_suggest(es_service, "nar")                    # All types
    test_suggest(es_service, "saber", ["anime"])         # Only anime
    test_suggest(es_service, "one p")                  # One Piece
    test_suggest(es_service, "luf")                    # Luffy (character)
    test_suggest(es_service, "attack")                 # Attack on Titan
    test_suggest(es_service, "madh", ["studio"])       # Madhouse studio
    test_suggest(es_service, "school", ["theme"])      # School theme
    test_suggest(es_service, "action", ["genre"])      # Action genre
    test_suggest(es_service, "titan", ["anime"])      # Action genre

    print("Testing complete!")
