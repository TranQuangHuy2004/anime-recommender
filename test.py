from services.elasticsearch_service import ElasticsearchService
from elasticsearch import Elasticsearch

# Simple test
es = Elasticsearch(["http://localhost:9200"], verify_certs=False)
print(f"Ping: {es.ping()}")  # Should print True

# Test with your exact connection settings
es_service = ElasticsearchService()
