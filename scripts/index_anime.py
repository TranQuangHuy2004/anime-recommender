from services.elasticsearch_service import ElasticsearchService
from services.database import Database
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Elasticsearch indexing script"
    )

    parser.add_argument("--delete", action="store_true", help="Delete all Elasticsearch indices before indexing")

    args = parser.parse_args()

    print("=" * 50)
    print("ELASTICSEARCH INDEXING SCRIPT")
    print("=" * 50)

    # Check if Elasticsearch is running
    es = ElasticsearchService()

    # Delete indices if requested
    if args.delete:
        print("\n⚠️ Deleting all Elasticsearch indices...")
        es.delete_indices()

    # Connect to database
    print("Connecting to PostgreSQL...")
    db = Database()

    # Index all
    print("\n" + "=" * 30)
    print("INDEXING ANIME DATA")
    print("=" * 30)

    es.index_all_data(db)
