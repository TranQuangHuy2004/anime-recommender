from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError
from utils.helpers import extract_year_month_season
import os
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ElasticsearchService:
    def __init__(self):
        self.host = os.getenv("ES_HOST", "localhost")
        self.port = os.getenv("ES_PORT", "9200")

        # Define all indices
        self.indices = {
            'anime': 'anime_index',
            'search_suggestions': 'search_suggestions_index'
        }

        # Connection
        self.es = Elasticsearch(
            [f"http://{self.host}:{self.port}"],
            # Add these parameters:
            request_timeout=60,
            max_retries=5,
            retry_on_timeout=True,
            # For Elasticsearch 8.x:
            verify_certs=False,  # Since you disabled SSL
            ssl_show_warn=False
        )

        self._test_connection()

    def _test_connection(self):
        try:
            if self.es.ping():
                logger.info("✅ Connected to Elasticsearch server")
            else:
                logger.error("❌ Cannot connect to Elasticsearch")
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection failed: {e}")

    def create_all_indices(self):
        """Create all indices with proper mappings"""
        logger.info("Creating all Elasticsearch indices...")

        self.create_anime_index()
        self.create_search_suggestions_index()

    def create_anime_index(self):
        """Create anime index with nested objects for relationships"""
        if self.es.indices.exists(index=self.indices['anime']):
            logger.info(f"Index {self.indices['anime']} already exists")
            return

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "anime_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding", "english_stop", "english_stemmer"]
                        },
                        "japanese_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding", "ja_stop"]
                        }
                        # "edge_ngram_analyzer": {
                        #     "type": "custom",
                        #     "tokenizer": "standard",
                        #     "filter": ["lowercase", "edge_ngram_filter"]
                        # }
                    },
                    "filter": {
                        # "edge_ngram_filter": {
                        #     "type": "edge_ngram",
                        #     "min_gram": 2,
                        #     "max_gram": 10
                        # },
                        "english_stop": {"type": "stop", "stopwords": "_english_"},
                        "english_stemmer": {"type": "stemmer", "language": "english"},
                        "ja_stop": {"type": "stop", "stopwords": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある"]}
                    }
                }
            },
            "mappings": {
                "properties": {
                    # Core identifier
                    "mal_id": {"type": "integer"},

                    # Titles
                    "title": {
                        "type": "text",
                        "analyzer": "anime_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "japanese": {"type": "text", "analyzer": "japanese_analyzer"},
                            # "suggest": {"type": "completion"}
                        }
                    },
                    "title_english": {
                        "type": "text",
                        "analyzer": "anime_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                            # "suggest": {"type": "completion"}
                        }
                    },
                    "title_japanese": {
                        "type": "text",
                        "analyzer": "japanese_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "title_synonyms": {
                        "type": "keyword",  # Each array item is separate exact value
                        "fields": {
                            "text": {"type": "text", "analyzer": "anime_analyzer"}  # For fuzzy search
                        }
                    },

                    # Description
                    "synopsis": {"type": "text", "analyzer": "anime_analyzer"},

                    # Metadata
                    "type": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "rating": {"type": "keyword"},

                    # Stats
                    "score": {"type": "float"},
                    "popularity": {"type": "integer"},
                    "episodes": {"type": "integer"},
                    "duration": {"type": "keyword", "index": False},
                    "duration_minutes": {"type": "integer"},  # Extracted number, e.g., 24 from "24 min per ep"

                    # Temporal
                    "season": {"type": "keyword"},
                    "year": {"type": "integer"},
                    "aired_string": {"type": "keyword", "index": False},

                    # Media
                    "image_url": {"type": "keyword", "index": False},
                    "trailer_url": {"type": "keyword", "index": False},

                    # Nested relationships (complete data)
                    "studios": {
                        "type": "nested",
                        "properties": {
                            "mal_id": {"type": "integer"},
                            "name": {"type": "keyword"},
                            "name_search": {"type": "text", "analyzer": "anime_analyzer"}
                        }
                    },
                    "genres": {
                        "type": "nested",
                        "properties": {
                            "mal_id": {"type": "integer"},
                            "name": {"type": "keyword"},
                            "name_search": {"type": "text", "analyzer": "anime_analyzer"}
                        }
                    },
                    "themes": {
                        "type": "nested",
                        "properties": {
                            "mal_id": {"type": "integer"},
                            "name": {"type": "keyword"},
                            "name_search": {"type": "text", "analyzer": "anime_analyzer"}
                        }
                    },
                    "demographics": {
                        "type": "nested",
                        "properties": {
                            "mal_id": {"type": "integer"},
                            "name": {"type": "keyword"},
                            "name_search": {"type": "text", "analyzer": "anime_analyzer"}
                        }
                    },
                    "characters": {
                        "type": "nested",
                        "properties": {
                            "mal_id": {"type": "integer"},
                            "name": {"type": "text", "analyzer": "anime_analyzer"},
                            "role": {"type": "keyword"},
                            "favorites": {"type": "integer"},
                            "image_url": {"type": "keyword", "index": False},
                            "voice_actors": {
                                "type": "object",
                                "properties": {
                                    "mal_id": {"type": "integer"},
                                    "name": {"type": "text", "analyzer": "anime_analyzer"},
                                    "image_url": {"type": "keyword", "index": False}
                                },
                                "enabled": False
                            }
                        }
                    },

                    # For quick filtering
                    "studio_names": {"type": "keyword"},
                    "genre_names": {"type": "keyword"},
                    "theme_names": {"type": "keyword"},
                    "demographic_names": {"type": "keyword"},
                    "character_names": {"type": "keyword"},
                    # "voice_actor_names": {"type": "keyword"},

                    # Computed fields
                    "is_popular": {"type": "boolean"},
                    "score_range": {"type": "keyword"},
                    "episode_range": {"type": "keyword"}
                }
            }
        }

        try:
            self.es.indices.create(index=self.indices['anime'], body=mapping)
            logger.info(f"✅ Created anime index: {self.indices['anime']}")
        except Exception as e:
            logger.error(f"❌ Error creating anime index: {e}")

    def create_search_suggestions_index(self):
        """Create index for autocomplete/search suggestions"""
        if self.es.indices.exists(index=self.indices['search_suggestions']):
            logger.info(f"Index {self.indices['search_suggestions']} already exists")
            return

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "autocomplete_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "autocomplete_filter"]
                        }
                    },
                    "filter": {
                        "autocomplete_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 10
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "type": {"type": "keyword"},  # anime, character, studio, genre, voice_actor
                    "mal_id": {"type": "integer"},
                    "main_name": {"type": "keyword", "index": False},
                    "search_full_names": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "search_key_names": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "subtype": {"type": "keyword"},  # TV, Movie, etc. for anime
                    "score": {"type": "float"},
                    "popularity": {"type": "integer"},
                    "image_url": {"type": "keyword", "index": False},
                    "suggest": {
                        "type": "completion",
                        "contexts": [
                            {
                                "name": "entity_type",
                                "type": "category"
                            }
                        ]
                    }
                }
            }
        }

        try:
            self.es.indices.create(index=self.indices['search_suggestions'], body=mapping)
            logger.info(f"✅ Created search suggestions index: {self.indices['search_suggestions']}")
        except Exception as e:
            logger.error(f"❌ Error creating search suggestions index: {e}")

    def index_all_data(self, db_service):
        """Index all data from database"""
        logger.info("Starting comprehensive data indexing...")

        # Create all indices
        self.create_all_indices()

        # Index in order
        results = {}
        # Add refresh control for faster indexing
        self.es.indices.put_settings(
            index=self.indices['anime'],
            body={"index": {"refresh_interval": "-1"}}
        )

        # Index anime
        results['anime'] = self.index_anime_complete(db_service)
        # Index search suggestions
        results['search_suggestions'] = self.index_search_suggestions(db_service)

        self.es.indices.put_settings(
            index=self.indices['anime'],
            body={"index": {"refresh_interval": "1s"}}
        )

        # Print summary
        time.sleep(5)
        self.print_indexing_summary(results)

        return results

    def index_anime_complete(self, db_service):
        """Index anime with ALL relationship data"""
        logger.info("Indexing anime with all relationships...")

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM anime"
        result = db_service.execute_query(count_query)
        total_anime = result[0]['total'] if result else 0

        indexed = 0
        batch_size = int(os.getenv("ES_BATCH_SIZE", 500))
        offset = 0

        with tqdm(total=total_anime, desc="Indexing anime") as pbar:
            while offset < total_anime:
                # Complex query to get all relationship data
                query = """
                WITH ranked_characters AS (
                    SELECT
                        ac.anime_id,
                        c.mal_id AS character_mal_id,
                        c.name AS character_name,
                        c.image_url AS character_image_url,
                        c.favorites,
                        ac.role,
                        ROW_NUMBER() OVER (
                            PARTITION BY ac.anime_id
                            ORDER BY c.favorites DESC NULLS LAST
                        ) AS rn
                    FROM anime_characters ac
                    JOIN characters c ON ac.character_id = c.mal_id
                ),
                top_characters AS (
                    SELECT *
                    FROM ranked_characters
                    WHERE rn <= 10
                ),
                character_voice_actors AS (
                    SELECT
                        acva.anime_id,
                        acva.character_id,
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'mal_id', va.mal_id,
                                'name', va.name,
                                'image_url', va.image_url
                            )
                        ) AS voice_actors
                    FROM anime_character_voice_actors acva
                    JOIN voice_actors va ON acva.voice_actor_id = va.mal_id
                    WHERE va.language = 'Japanese'
                    GROUP BY acva.anime_id, acva.character_id
                ),
                anime_studios_agg AS (
                    SELECT
                        ast.anime_id,
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', s.mal_id,
                            'name', s.name
                        )) AS studios
                    FROM anime_studios ast
                    JOIN studios s ON ast.studio_id = s.mal_id
                    GROUP BY ast.anime_id
                ),
                anime_genres_agg AS (
                    SELECT
                        ag.anime_id,
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', g.mal_id,
                            'name', g.name
                        )) AS genres
                    FROM anime_genres ag
                    JOIN genres g ON ag.genre_id = g.mal_id
                    GROUP BY ag.anime_id
                ),
                anime_themes_agg AS (
                    SELECT
                        at2.anime_id,
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', t.mal_id,
                            'name', t.name
                        )) AS themes
                    FROM anime_themes at2
                    JOIN themes t ON at2.theme_id = t.mal_id
                    GROUP BY at2.anime_id
                ),
                anime_demographics_agg AS (
                    SELECT
                        ad.anime_id,
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', d.mal_id,
                            'name', d.name
                        )) AS demographics
                    FROM anime_demographics ad
                    JOIN demographics d ON ad.demographic_id = d.mal_id
                    GROUP BY ad.anime_id
                ),
                sorted_top_characters AS (
                    SELECT
                        tc.anime_id,
                        tc.character_mal_id,
                        tc.character_name,
                        tc.character_image_url,
                        tc.favorites,
                        tc.role,
                        COALESCE(cva.voice_actors, '[]'::json) AS voice_actors
                    FROM top_characters tc
                    LEFT JOIN character_voice_actors cva
                        ON tc.anime_id = cva.anime_id
                        AND tc.character_mal_id = cva.character_id
                    ORDER BY tc.favorites DESC NULLS LAST
                ),
                anime_characters_agg AS (
                    SELECT
                        anime_id,
                        json_agg(
                            jsonb_build_object(
                                'mal_id', character_mal_id,
                                'name', character_name,
                                'role', role,
                                'favorites', favorites,
                                'image_url', character_image_url,
                                'voice_actors', voice_actors
                            )
                        ) AS characters
                    FROM sorted_top_characters
                    GROUP BY anime_id
                )
                SELECT
                    a.*,
                    COALESCE(asa.studios, '[]'::json) AS studios,
                    COALESCE(aga.genres, '[]'::json) AS genres,
                    COALESCE(ata.themes, '[]'::json) AS themes,
                    COALESCE(ada.demographics, '[]'::json) AS demographics,
                    COALESCE(aca.characters, '[]'::json) AS characters
                FROM anime a
                LEFT JOIN anime_studios_agg asa ON a.mal_id = asa.anime_id
                LEFT JOIN anime_genres_agg aga ON a.mal_id = aga.anime_id
                LEFT JOIN anime_themes_agg ata ON a.mal_id = ata.anime_id
                LEFT JOIN anime_demographics_agg ada ON a.mal_id = ada.anime_id
                LEFT JOIN anime_characters_agg aca ON a.mal_id = aca.anime_id
                ORDER BY a.mal_id
                LIMIT %s OFFSET %s
                """

                results = db_service.execute_query(query, (batch_size, offset))

                if not results:
                    break

                actions = []
                for anime in results:
                    # Compute derived fields
                    is_popular = anime['popularity'] <= 1000 if anime['popularity'] else False

                    score_range = 'unknown'
                    if anime['score']:
                        if anime['score'] >= 9.0:
                            score_range = '9+'
                        elif anime['score'] >= 8.0:
                            score_range = '8-9'
                        elif anime['score'] >= 7.0:
                            score_range = '7-8'
                        elif anime['score'] >= 6.0:
                            score_range = '6-7'
                        else:
                            score_range = '0-6'

                    episode_range = 'unknown'
                    if anime['episodes']:
                        if anime['episodes'] == 1:
                            episode_range = 'movie'
                        elif anime['episodes'] <= 12:
                            episode_range = 'short'
                        elif anime['episodes'] <= 24:
                            episode_range = 'medium'
                        else:
                            episode_range = 'long'

                    year = None
                    season = None
                    result = extract_year_month_season(anime.get('aired_string'))
                    if result:
                        year = result[0]
                        season = result[1]

                    action = {
                        "_index": self.indices['anime'],
                        "_id": anime['mal_id'],
                        "_source": {
                            "mal_id": anime['mal_id'],
                            "title": anime['title'],
                            "title_english": anime['title_english'],
                            "title_japanese": anime['title_japanese'],
                            "title_synonyms": anime.get('title_synonyms', []),
                            "synopsis": anime.get('synopsis', ''),
                            "type": anime.get('type'),
                            "source": anime.get('source'),
                            "status": anime.get('status'),
                            "score": anime.get('score'),
                            "popularity": anime.get('popularity'),
                            "episodes": anime.get('episodes'),
                            "duration": anime.get('duration'),
                            "duration_minutes": extract_minutes_from_duration(anime.get('duration')),
                            "rating": anime.get('rating'),
                            "season": anime['season'] if anime.get('season', '') else season,
                            "year": anime['year'] if anime.get('year', '') else year,
                            "aired_string": anime.get('aired_string'),
                            "image_url": anime.get('image_url'),
                            "trailer_url": anime.get('trailer_url'),

                            # Nested relationships
                            "studios": anime.get('studios', []),
                            "genres": anime.get('genres', []),
                            "themes": anime.get('themes', []),
                            "demographics": anime.get('demographics', []),
                            "characters": anime.get('characters', []),

                            # Flat arrays for filtering
                            "studio_names": [s['name'] for s in anime.get('studios', [])],
                            "genre_names": [g['name'] for g in anime.get('genres', [])],
                            "theme_names": [t['name'] for t in anime.get('themes', [])],
                            "demographic_names": [d['name'] for d in anime.get('demographics', [])],
                            "character_names": [c['name'] for c in anime.get('characters', [])],
                            # "voice_actor_names": list(set(
                            #     va['name']
                            #     for c in anime.get('characters', [])
                            #     for va in c.get('voice_actors', [])
                            # )),

                            # Computed fields
                            "is_popular": is_popular,
                            "score_range": score_range,
                            "episode_range": episode_range
                        }
                    }
                    actions.append(action)

                if actions:
                    success, failed = helpers.bulk(self.es, actions, stats_only=True, raise_on_error=False)
                    if failed:
                        logger.warning(f"{failed} documents failed indexing")
                    indexed += success

                offset += batch_size
                pbar.update(len(results))
                # time.sleep(0.1)

        logger.info(f"Indexed {indexed} anime with complete relationships")
        return indexed

    def index_search_suggestions(self, db_service):
        """Index all searchable entities for autocomplete"""
        logger.info("Indexing search suggestions...")

        actions = []

        # 1. Anime
        anime_query = """
        SELECT 
            a.mal_id,
            a.title,
            a.title_english,
            a.title_synonyms,
            a.type,
            a.score,
            a.popularity,
            a.image_url,
            COALESCE(
                (
                    SELECT json_agg(sub.name ORDER BY sub.favorites DESC)
                    FROM (
                        SELECT 
                            c.name, 
                            c.favorites
                        FROM anime_characters ac
                        JOIN characters c ON ac.character_id = c.mal_id
                        WHERE ac.anime_id = a.mal_id
                        AND c.name IS NOT NULL
                        ORDER BY c.favorites DESC NULLS LAST
                        LIMIT 20
                    ) sub
                ), 
                '[]'::json
            ) AS top_characters
        FROM anime a
        LEFT JOIN anime_characters ac ON a.mal_id = ac.anime_id
        LEFT JOIN characters c ON ac.character_id = c.mal_id
        WHERE a.title IS NOT NULL
        GROUP BY a.mal_id
        ORDER BY a.popularity ASC
        """

        anime_results = db_service.execute_query(anime_query)
        for anime in anime_results:
            # Base input for anime titles
            title = anime['title']
            title_english = anime.get('title_english') or ''
            synonyms = anime.get('title_synonyms', []) or []  # Ensure it's always a list

            fullnames = [title]
            keynames = [title, *title.strip().split()]

            if title_english:
                fullnames.append(title_english)
                keynames.append(title_english)
                keynames.extend(title_english.strip().split())

            if synonyms:
                fullnames.extend(synonyms)
                keynames.extend(synonyms)
                for syn in synonyms:
                    if syn:
                        keynames.extend(syn.strip().split())

            # Character inputs -> Find anime based on character names
            char_inputs = set()  # Use set to avoid duplicates
            raw_chars = anime.get('top_characters', [])[:20]  # Limit to top 10

            for full_name in raw_chars:
                if not full_name:
                    continue
                full_name = full_name.strip()
                # Always add the raw/official name
                char_inputs.add(full_name)
                # Reversal logic for "Last, First" formats (common on MAL)
                if ', ' in full_name:
                    parts = full_name.split(', ', 1)
                    if len(parts) == 2:
                        last = parts[0].strip()
                        first = parts[1].strip()
                        # Add "First Last" (Western order)
                        char_inputs.add(f"{first} {last}")
                        # Add first name only (most common user search!)
                        char_inputs.add(first)
                        # Add last name only
                        char_inputs.add(last)

            keynames = keynames + list(char_inputs)

            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"anime_{anime['mal_id']}",
                "_source": {
                    "type": "anime",
                    "mal_id": anime['mal_id'],
                    "main_name": title,
                    "search_full_names": fullnames,
                    "search_key_names": keynames,
                    "subtype": anime['type'],
                    "score": anime['score'],
                    "popularity": anime['popularity'],
                    "image_url": anime.get("image_url"),
                    "suggest": {
                        "input": title,
                        "weight": 1000 - min(anime['popularity'], 999) if anime['popularity'] else 100,
                        "contexts": {
                            "entity_type": ["anime", anime['type'] or "unknown", "global"]
                        }
                    }
                }
            })

        # 3. Studios
        studios_query = """
        SELECT 
            s.mal_id,
            s.name
        FROM studios s
        WHERE s.name IS NOT NULL
        """

        studio_results = db_service.execute_query(studios_query)
        for studio in studio_results:
            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"studio_{studio['mal_id']}",
                "_source": {
                    "type": "studio",
                    "mal_id": studio['mal_id'],
                    "main_name": studio['name'],
                    "search_full_names": studio['name'],
                    "search_key_names": studio['name'].strip().split(),
                    "suggest": {
                        "input": [studio['name']],
                        "weight": 500,
                        "contexts": {"entity_type": ["studio", "global"]}
                    }
                }
            })

        # 4. Genres
        genres_query = """
        SELECT 
            g.mal_id,
            g.name
        FROM genres g
        WHERE g.name IS NOT NULL
        """

        genre_results = db_service.execute_query(genres_query)
        for genre in genre_results:
            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"genre_{genre['mal_id']}",
                "_source": {
                    "type": "genre",
                    "mal_id": genre['mal_id'],
                    "main_name": genre['name'],
                    "search_full_names": genre['name'],
                    "search_key_names": genre['name'].strip().split(),
                    "suggest": {
                        "input": [genre['name']],
                        "weight": 500,
                        "contexts": {"entity_type": ["genre", "global"]}
                    }
                }
            })

        # 5. Themes
        themes_query = """
        SELECT 
            t.mal_id,
            t.name
        FROM themes t
        WHERE t.name IS NOT NULL
        """

        theme_results = db_service.execute_query(themes_query)
        for theme in theme_results:
            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"theme_{theme['mal_id']}",
                "_source": {
                    "type": "theme",
                    "mal_id": theme['mal_id'],
                    "main_name": theme['name'],
                    "search_full_names": theme['name'],
                    "search_key_names": theme['name'].strip().split(),
                    "suggest": {
                        "input": [theme['name']],
                        "weight": 500,
                        "contexts": {"entity_type": ["theme", "global"]}
                    }
                }
            })

        # 6. Demographics
        demographics_query = """
        SELECT 
            d.mal_id,
            d.name
        FROM demographics d
        WHERE d.name IS NOT NULL
        """

        demographic_results = db_service.execute_query(demographics_query)
        for demographic in demographic_results:
            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"demographic_{demographic['mal_id']}",
                "_source": {
                    "type": "demographic",
                    "mal_id": demographic['mal_id'],
                    "main_name": demographic['name'],
                    "search_full_names": demographic['name'],
                    "search_key_names": demographic['name'].strip().split(),
                    "search_name": demographic['name'],
                    "suggest": {
                        "input": [demographic['name']],
                        "weight": 500,
                        "contexts": {"entity_type": ["demographic", "global"]}
                    }
                }
            })

        # Bulk index
        batch_size = int(os.getenv("ES_BATCH_SIZE", 500))
        total_success = 0
        total_failed = 0

        if actions:
            with tqdm(total=len(actions), desc="Index search_suggestions") as pbar:
                for batch_num, batch in enumerate(chunked(actions, batch_size), start=1):
                    try:
                        success, failed = helpers.bulk(self.es, batch, stats_only=True, raise_on_error=False)

                        total_success += success
                        total_failed += failed

                    except Exception as e:
                        logger.error(f"❌ Bulk indexing failed on batch {batch_num}: {e}")

                    pbar.update(success)

            logger.info(
                f"✅ Finished indexing search suggestions. "
                f"Success={total_success}, Failed={total_failed}"
            )

            return total_success

        return 0

    def print_indexing_summary(self, results):
        """Print indexing summary"""
        print("\n" + "=" * 60)
        print("ELASTICSEARCH INDEXING SUMMARY")
        print("=" * 60)

        for index_name, count in results.items():
            print(f"{index_name:20} {count:,} documents")

        # Get index sizes
        try:
            stats = self.es.indices.stats()
            print("\n" + "=" * 60)
            print("INDEX SIZES")
            print("=" * 60)

            for index in self.indices.values():
                if index in stats['indices']:
                    docs = stats['indices'][index]['total']['docs']['count']
                    size_bytes = stats['indices'][index]['total']['store']['size_in_bytes']
                    size_mb = size_bytes / (1024 * 1024)
                    print(f"{index:25} {docs:,} docs, {size_mb:.2f} MB")
        except Exception as e:
            logger.error(f"Error getting stats: {e}")

    def search_anime(self, query=None, filters=None, size=50, page=1):
        """Search anime with optional filters and pagination"""
        if not filters:
            filters = {}

        from_ = (page - 1) * size

        search_body = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "from": from_,
            "size": size,
            "sort": [
                {"_score": {"order": "desc"}},
                {"popularity": {"order": "asc"}},
                {"score": {"order": "desc"}}
            ],
            "aggs": {
                "genres": {"terms": {"field": "genre_names", "size": 20}},
                "types": {"terms": {"field": "type", "size": 10}},
                "seasons": {"terms": {"field": "season", "size": 10}},
                "years": {"histogram": {"field": "year", "interval": 1}},
                "score_ranges": {"terms": {"field": "score_range", "size": 5}}
            }
        }

        # Add text search
        if query and query.strip():
            search_body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "title_english^2",
                        "synopsis",
                        "title_synonyms.text^1.5",
                        "character_names"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            })
        else:
            search_body["query"]["bool"]["must"].append({"match_all": {}})

        # ========== FILTERS ==========

        # Type filter
        if filters.get('type') and filters['type'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"type": filters['type']}
            })

        # Year range filter
        if filters.get('year_from') or filters.get('year_to'):
            year_range = {}
            if filters.get('year_from'):
                year_range['gte'] = filters['year_from']
            if filters.get('year_to'):
                year_range['lte'] = filters['year_to']
            search_body["query"]["bool"]["filter"].append({
                "range": {"year": year_range}
            })

        # Score filter
        if filters.get('min_score'):
            search_body["query"]["bool"]["filter"].append({
                "range": {"score": {"gte": filters['min_score']}}
            })

        # Season filter
        if filters.get('season') and filters['season'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"season": filters['season']}
            })

        # Status filter
        if filters.get('status') and filters['status'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"status": filters['status']}
            })

        # Source filter
        if filters.get('source') and filters['source'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"source": filters['source']}
            })

        # Rating filter
        if filters.get('rating') and filters['rating'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"rating": filters['rating']}
            })

        # Episode count filters
        if filters.get('min_episodes'):
            search_body["query"]["bool"]["filter"].append({
                "range": {"episodes": {"gte": filters['min_episodes']}}
            })

        if filters.get('max_episodes'):
            search_body["query"]["bool"]["filter"].append({
                "range": {"episodes": {"lte": filters['max_episodes']}}
            })

        # Duration filter (in minutes)
        if filters.get('min_duration'):
            search_body["query"]["bool"]["filter"].append({
                "range": {"duration_minutes": {"gte": filters['min_duration']}}
            })

        if filters.get('max_duration'):
            search_body["query"]["bool"]["filter"].append({
                "range": {"duration_minutes": {"lte": filters['max_duration']}}
            })

        # Studio filter
        if filters.get('studios'):
            search_body["query"]["bool"]["filter"].append({
                "terms": {"studio_names": filters['studios']}
            })

        # Genre filter
        if filters.get('genres'):
            search_body["query"]["bool"]["filter"].append({
                "terms": {"genre_names": filters['genres']}
            })

        # Theme filter
        if filters.get('themes'):
            search_body["query"]["bool"]["filter"].append({
                "terms": {"theme_names": filters['themes']}
            })

        # Demographic filter
        if filters.get('demographics'):
            search_body["query"]["bool"]["filter"].append({
                "terms": {"demographic_names": filters['demographics']}
            })

        # Popular only filter
        if filters.get('popular_only'):
            search_body["query"]["bool"]["filter"].append({
                "term": {"is_popular": True}
            })

        # Score range filter (pre-computed)
        if filters.get('score_range') and filters['score_range'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"score_range": filters['score_range']}
            })

        # Episode range filter (pre-computed)
        if filters.get('episode_range') and filters['episode_range'] != "All":
            search_body["query"]["bool"]["filter"].append({
                "term": {"episode_range": filters['episode_range']}
            })

        try:
            response = self.es.search(index=self.indices['anime'], body=search_body)

            # Format results
            results = {
                'total': response['hits']['total']['value'],
                'hits': [],
                'aggregations': response.get('aggregations', {}),
                'page': page,
                'total_pages': (response['hits']['total']['value'] + size - 1) // size,
                'size': size
            }

            for hit in response['hits']['hits']:
                anime = hit['_source']
                anime['_score'] = hit['_score']
                results['hits'].append(anime)

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'total': 0, 'hits': [], 'aggregations': {}, 'page': page, 'total_pages': 0}

    def get_search_suggestions_for_streamlit(self, searchterm, search_type="all", limit=10):
        """
        Search function that uses the completion suggester and always includes a "raw/full-text search" option as the first suggestion.
        """
        if not searchterm or len(searchterm.strip()) < 2:
            return []

        suggestions = []

        # Raw search always first
        suggestions.append((
            f"🔍 Search for '{searchterm}'",
            {"raw_search": True, "query": searchterm.strip()}
        ))

        try:
            must_filters = []
            if search_type != "all" and search_type != "All":
                must_filters.append({
                    "term": {"type": search_type.lower()}
                })

            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": searchterm,
                                    "fields": [
                                        "search_full_names^6",
                                        "search_key_names^4"
                                    ],
                                    "operator": "and",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ],
                        "filter": must_filters
                    }
                },
                "size": limit
            }

            response = self.es.search(
                index=self.indices['search_suggestions'],
                body=body
            )

            hits = response['hits']['hits']
            seen = set()

            for hit in hits:
                source = hit['_source']
                entity_type = source['type']
                entity_id = f"{entity_type}_{source['mal_id']}"

                if entity_id in seen:
                    continue
                seen.add(entity_id)

                display_text = self._format_suggestion_display(source, entity_type)

                value_dict = {
                    'id': source['mal_id'],
                    'name': source['main_name'],
                    'type': entity_type.capitalize(),
                    'raw_type': entity_type,
                    'score': source.get('score'),
                    'popularity': source.get('popularity'),
                    'image_url': source.get('image_url'),
                    'subtype': source.get('subtype'),
                    '_score': hit['_score'],
                    'search_term': searchterm,
                    'selected_via_suggestion': True,
                }

                suggestions.append((display_text, value_dict))

                if len(suggestions) >= limit + 1:
                    break

            return suggestions

        except Exception as e:
            logger.error(f"Error in streamlit search function: {e}")
            return suggestions

    def _format_suggestion_display(self, source, entity_type):
        """Format the display text for suggestions"""
        t = f"{entity_type.capitalize()}:"
        if entity_type == "anime":
            display = f"🎬 {t} {source['main_name']}"
            if source.get('subtype'):
                display += f" ({source.get('subtype')})"
            if source.get('score'):
                display += f" ⭐ {source['score']:.1f}"
            return display
        elif entity_type == "studio":
            return f"🏢 {t} {source['main_name']}"
        elif entity_type == "genre":
            return f"🏷️ {t} {source['main_name']}"
        elif entity_type == "theme":
            return f"🎭 {t} {source['main_name']}"
        elif entity_type == "demographic":
            return f"👥 {t} {source['main_name']}"
        else:
            return f"{source['main_name']}"

    def get_anime_by_mal_id(self, mal_id):
        """Get anime by MAL ID"""
        try:
            response = self.es.get(index=self.indices['anime'], id=mal_id)
            return response['_source']
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting anime {mal_id}: {e}")
            return None

    def get_studio_anime(self, studio_name, size=50):
        """Get anime by studio"""
        search_body = {
            "query": {
                "term": {
                    "studio_names": studio_name
                }
            },
            "size": size,
            "sort": [{"popularity": {"order": "asc"}}]
        }

        try:
            response = self.es.search(index=self.indices['anime'], body=search_body)

            # Format results consistently with search_anime()
            results = {
                'total': response['hits']['total']['value'],
                'hits': [],
                'page': 1,
                'total_pages': (response['hits']['total']['value'] + size - 1) // size,
                'size': size
            }

            for hit in response['hits']['hits']:
                anime = hit['_source']
                anime['_score'] = hit['_score']
                results['hits'].append(anime)

            return results

        except Exception as e:
            logger.error(f"Genre search error: {e}")
            return {'total': 0, 'hits': [], 'page': 1, 'total_pages': 0}

    def get_genre_anime(self, genre_name, size=50):
        """Get anime by genre"""
        search_body = {
            "query": {
                "term": {
                    "genre_names": genre_name
                }
            },
            "size": size,
            "sort": [{"popularity": {"order": "asc"}}]
        }

        try:
            response = self.es.search(index=self.indices['anime'], body=search_body)

            # Format results consistently with search_anime()
            results = {
                'total': response['hits']['total']['value'],
                'hits': [],
                'page': 1,
                'total_pages': (response['hits']['total']['value'] + size - 1) // size,
                'size': size
            }

            for hit in response['hits']['hits']:
                anime = hit['_source']
                anime['_score'] = hit['_score']
                results['hits'].append(anime)

            return results

        except Exception as e:
            logger.error(f"Genre search error: {e}")
            return {'total': 0, 'hits': [], 'page': 1, 'total_pages': 0}

    def get_theme_anime(self, theme_name, size=50):
        """Get anime by theme"""
        search_body = {
            "query": {
                "term": {
                    "theme_names": theme_name
                }
            },
            "size": size,
            "sort": [{"popularity": {"order": "asc"}}]
        }

        try:
            response = self.es.search(index=self.indices['anime'], body=search_body)

            # Format results consistently with search_anime()
            results = {
                'total': response['hits']['total']['value'],
                'hits': [],
                'page': 1,
                'total_pages': (response['hits']['total']['value'] + size - 1) // size,
                'size': size
            }

            for hit in response['hits']['hits']:
                anime = hit['_source']
                anime['_score'] = hit['_score']
                results['hits'].append(anime)

            return results

        except Exception as e:
            logger.error(f"Genre search error: {e}")
            return {'total': 0, 'hits': [], 'page': 1, 'total_pages': 0}

    def get_demographic_anime(self, demographic_name, size=50):
        """Get anime by demographic"""
        search_body = {
            "query": {
                "term": {
                    "demographic_names": demographic_name
                }
            },
            "size": size,
            "sort": [{"popularity": {"order": "asc"}}]
        }

        try:
            response = self.es.search(index=self.indices['anime'], body=search_body)

            # Format results consistently with search_anime()
            results = {
                'total': response['hits']['total']['value'],
                'hits': [],
                'page': 1,
                'total_pages': (response['hits']['total']['value'] + size - 1) // size,
                'size': size
            }

            for hit in response['hits']['hits']:
                anime = hit['_source']
                anime['_score'] = hit['_score']
                results['hits'].append(anime)

            return results

        except Exception as e:
            logger.error(f"Genre search error: {e}")
            return {'total': 0, 'hits': [], 'page': 1, 'total_pages': 0}

    def get_filter_options(self, db_service):
        """Get all available filter options from database"""
        options = {}

        # Get all genres
        genre_query = "SELECT name FROM genres ORDER BY name"
        genres = db_service.execute_query(genre_query)
        options['genres'] = [g['name'] for g in genres] if genres else []

        # Get all types
        type_query = "SELECT DISTINCT type FROM anime WHERE type IS NOT NULL ORDER BY type"
        types = db_service.execute_query(type_query)
        options['types'] = [t['type'] for t in types] if types else []

        # Get all statuses
        status_query = "SELECT DISTINCT status FROM anime WHERE status IS NOT NULL ORDER BY status"
        statuses = db_service.execute_query(status_query)
        options['statuses'] = [s['status'] for s in statuses] if statuses else []

        # Get all seasons
        season_query = "SELECT DISTINCT season FROM anime WHERE season IS NOT NULL ORDER BY season"
        seasons = db_service.execute_query(season_query)
        options['seasons'] = [s['season'] for s in seasons] if seasons else []

        # Get all sources
        source_query = "SELECT DISTINCT source FROM anime WHERE source IS NOT NULL ORDER BY source"
        sources = db_service.execute_query(source_query)
        options['sources'] = [s['source'] for s in sources] if sources else []

        # Get all ratings
        rating_query = "SELECT DISTINCT rating FROM anime WHERE rating IS NOT NULL ORDER BY rating"
        ratings = db_service.execute_query(rating_query)
        options['ratings'] = [r['rating'] for r in ratings] if ratings else []

        # Get all studios
        studio_query = "SELECT name FROM studios ORDER BY name"
        studios = db_service.execute_query(studio_query)
        options['studios'] = [s['name'] for s in studios] if studios else []

        # Get year range
        year_query = "SELECT MIN(year) as min_year, MAX(year) as max_year FROM anime WHERE year IS NOT NULL"
        year_result = db_service.execute_query(year_query)
        if year_result and year_result[0]['min_year']:
            options['year_range'] = (year_result[0]['min_year'], year_result[0]['max_year'])

        # Score ranges
        options['score_ranges'] = [
            "All", "9+", "8-9", "7-8", "6-7", "0-6"
        ]

        # Episode ranges
        options['episode_ranges'] = [
            "All", "movie", "short", "medium", "long"
        ]

        return options

    def advanced_search(self, query=None, filters=None, sort_by="score",
                        order="desc", page=1, size=50):
        """Advanced search with custom sorting"""
        if not filters:
            filters = {}

        result = self.search_anime(query, filters, size, page)

        # Custom sorting (beyond default score sorting)
        if sort_by == "popularity":
            result['hits'] = sorted(result['hits'],
                                    key=lambda x: x.get('popularity', 99999),
                                    reverse=(order == "desc"))
        elif sort_by == "year":
            result['hits'] = sorted(result['hits'],
                                    key=lambda x: x.get('year', 0),
                                    reverse=(order == "desc"))
        elif sort_by == "episodes":
            result['hits'] = sorted(result['hits'],
                                    key=lambda x: x.get('episodes', 0),
                                    reverse=(order == "desc"))
        elif sort_by == "title":
            result['hits'] = sorted(result['hits'],
                                    key=lambda x: x.get('title', '').lower(),
                                    reverse=(order == "desc"))

        return result

    def delete_indices(self):
        """Delete all indices (use with caution!)"""
        try:
            for index in self.indices.values():
                if self.es.indices.exists(index=index):
                    self.es.indices.delete(index=index)
                    logger.info(f"Deleted index: {index}")
            print("✅ All indices deleted\n")

        except Exception as e:
            logger.error(f"Error deleting indices: {e}")


def chunked(iterable, size):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def extract_minutes_from_duration(duration_str):
    """Extract minutes from duration string like '24 min per ep' or '1 hr 30 min'"""
    if not duration_str:
        return None

    duration_str = str(duration_str).lower()

    # Patterns to match
    patterns = [
        # "24 min per ep" → 24
        (r'(\d+)\s*min(?!\s*hr)', 1),
        # "1 hr 30 min" → 90 (1*60 + 30)
        (r'(\d+)\s*hr(?:\s*(\d+)\s*min)?', lambda m: int(m.group(1)) * 60 + (int(m.group(2)) if m.group(2) else 0)),
        # "1.5 hr" → 90
        (r'(\d+\.?\d*)\s*hr', lambda m: int(float(m.group(1)) * 60)),
        # "30 sec" → 0 (round to nearest minute)
        (r'(\d+)\s*sec', lambda m: 1 if int(m.group(1)) >= 30 else 0),
        # "2 cours" → ~48 minutes (assuming 24 min per ep * 12 eps = 288)
        (r'(\d+)\s*cour', lambda m: int(m.group(1)) * 288),
        # Just a number "24" → 24 (assume minutes)
        (r'^\s*(\d+)\s*$', 1),
    ]

    import re

    for pattern, multiplier in patterns:
        match = re.search(pattern, duration_str)
        if match:
            if callable(multiplier):
                return multiplier(match)
            else:
                return int(match.group(1)) * multiplier

    # Default: try to extract any number
    numbers = re.findall(r'\d+', duration_str)
    if numbers:
        return int(numbers[0])  # Take first number found

    return None
