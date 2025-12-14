#!/usr/bin/env python
"""
Test Elasticsearch functionality
"""
from services.elasticsearch_service import ElasticsearchService


def test_elasticsearch():
    print("=" * 50)
    print("ELASTICSEARCH TEST SCRIPT")
    print("=" * 50)

    es = ElasticsearchService()

    # Test 1: Basic search
    print("\n1. Testing basic anime search...")
    results = es.search_anime("naruto", size=5)
    print(f"Found {results['total']} results for 'naruto'")
    for i, hit in enumerate(results['hits'][:3], 1):
        print(f"  {i}. {hit['title']} (Score: {hit.get('score')})")

    # Test 2: Filtered search
    print("\n2. Testing filtered search (Action genre, score > 8)...")
    results = es.search_anime(
        query="",
        filters={
            'genres': ['Action'],
            'min_score': 8.0,
            'type': 'TV'
        },
        size=3
    )
    print(f"Found {results['total']} Action TV anime with score > 8")
    for i, hit in enumerate(results['hits'][:3], 1):
        print(f"  {i}. {hit['title']} (Score: {hit.get('score')})")

    # Test 3: Character search
    print("\n3. Testing character search...")
    characters = es.search_characters("luffy", size=3)
    print(f"Found {len(characters)} characters for 'luffy'")
    for i, char in enumerate(characters[:3], 1):
        char_data = char['_source']
        print(f"  {i}. {char_data['name']} - {char_data.get('anime_title', 'Unknown')}")

    # Test 4: Aggregations
    print("\n4. Testing aggregations...")
    results = es.search_anime("", size=1)
    if 'aggregations' in results:
        genres = results['aggregations'].get('genres', {}).get('buckets', [])[:5]
        print("Top 5 genres:")
        for genre in genres:
            print(f"  {genre['key']}: {genre['doc_count']}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_elasticsearch()
