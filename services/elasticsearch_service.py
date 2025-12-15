from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError
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
                    # "character_names": {"type": "keyword"},
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
                    "name": {
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
                        c.role,
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
                        ac.anime_id,
                        ac.character_id,
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'mal_id', va.mal_id,
                                'name', va.name,
                                'image_url', va.image_url
                            )
                        ) AS voice_actors
                    FROM anime_characters ac
                    JOIN voice_actors va ON ac.voice_actor_id = va.mal_id
                    WHERE va.language = 'Japanese'
                    GROUP BY ac.anime_id, ac.character_id
                )
                SELECT
                    a.*,

                    -- Studios
                    COALESCE(
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', s.mal_id,
                            'name', s.name
                        )) FILTER (WHERE s.mal_id IS NOT NULL),
                        '[]'::json
                    ) AS studios,

                    -- Genres
                    COALESCE(
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', g.mal_id,
                            'name', g.name
                        )) FILTER (WHERE g.mal_id IS NOT NULL),
                        '[]'::json
                    ) AS genres,

                    -- Themes
                    COALESCE(
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', t.mal_id,
                            'name', t.name
                        )) FILTER (WHERE t.mal_id IS NOT NULL),
                        '[]'::json
                    ) AS themes,

                    -- Demographics
                    COALESCE(
                        json_agg(DISTINCT jsonb_build_object(
                            'mal_id', d.mal_id,
                            'name', d.name
                        )) FILTER (WHERE d.mal_id IS NOT NULL),
                        '[]'::json
                    ) AS demographics,

                    -- Top 10 characters with voice actors
                    COALESCE(
                        json_agg(
                            jsonb_build_object(
                                'mal_id', tc.character_mal_id,
                                'name', tc.character_name,
                                'role', tc.role,
                                'favorites', tc.favorites,
                                'image_url', tc.character_image_url,
                                'voice_actors', COALESCE(cva.voice_actors, '[]'::json)
                            )
                            ORDER BY tc.favorites DESC NULLS LAST
                        ) FILTER (WHERE tc.character_mal_id IS NOT NULL),
                        '[]'::json
                    ) AS characters

                FROM anime a

                -- Studios
                LEFT JOIN anime_studios ast ON a.mal_id = ast.anime_id
                LEFT JOIN studios s ON ast.studio_id = s.mal_id

                -- Genres
                LEFT JOIN anime_genres ag ON a.mal_id = ag.anime_id
                LEFT JOIN genres g ON ag.genre_id = g.mal_id

                -- Themes
                LEFT JOIN anime_themes at2 ON a.mal_id = at2.anime_id
                LEFT JOIN themes t ON at2.theme_id = t.mal_id

                -- Demographics
                LEFT JOIN anime_demographics ad ON a.mal_id = ad.anime_id
                LEFT JOIN demographics d ON ad.demographic_id = d.mal_id

                -- Characters
                LEFT JOIN top_characters tc ON a.mal_id = tc.anime_id
                LEFT JOIN character_voice_actors cva
                    ON tc.anime_id = cva.anime_id
                    AND tc.character_mal_id = cva.character_id

                GROUP BY a.mal_id
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
                            "season": anime.get('season'),
                            "year": anime.get('year'),
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
                        LIMIT 10
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
            base_inputs = [
                anime['title'],
                anime['title_english'],
                *anime.get('title_synonyms', [])
            ]
            base_inputs = [i for i in base_inputs if i]

            # Character inputs -> Find anime based on character names
            char_inputs = set()  # Use set to avoid duplicates
            raw_chars = anime.get('top_characters', [])[:10]  # Limit to top 10

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

            all_inputs = base_inputs + list(char_inputs)

            actions.append({
                "_index": self.indices['search_suggestions'],
                "_id": f"anime_{anime['mal_id']}",
                "_source": {
                    "type": "anime",
                    "mal_id": anime['mal_id'],
                    "name": anime['title'],
                    "subtype": anime['type'],
                    "score": anime['score'],
                    "popularity": anime['popularity'],
                    "image_url": anime.get("image_url"),
                    "suggest": {
                        "input": all_inputs,
                        "weight": 1000 - min(anime['popularity'], 999) if anime['popularity'] else 100,
                        "contexts": {
                            "entity_type": ["anime", anime['type'] or "unknown", "global"]
                        }
                    }
                }
            })

        # # 2. Characters
        # chars_query = """
        # SELECT
        #     c.mal_id AS character_id,
        #     c.name AS character_name,
        #     json_agg(
        #         DISTINCT jsonb_build_object(
        #             'anime_id', a.mal_id,
        #             'title', a.title
        #         )
        #     ) as anime_list,  -- ✅ All anime in one field
        #     c.favorites,
        #     c.image_url
        # FROM characters c
        # JOIN anime_characters ac ON c.mal_id = ac.character_id
        # JOIN anime a ON ac.anime_id = a.mal_id
        # GROUP BY c.mal_id, c.name, c.favorites, c.image_url
        # ORDER BY c.favorites DESC
        # LIMIT 5000
        # """

        # char_results = db_service.execute_query(chars_query)
        # for char in char_results:
        #     full_name = char['character_name']  # e.g., "Monkey D., Luffy"

        #     # Split common patterns
        #     extra_inputs = []

        #     # If comma-separated (common for "Last, First")
        #     if ', ' in full_name:
        #         parts = full_name.split(', ', 1)
        #         last = parts[0].strip()
        #         first = parts[1].strip()
        #         # Add reversed: "First Last"
        #         extra_inputs.append(f"{first} {last}")
        #         # Add first name only (most useful!)
        #         extra_inputs.append(first)
        #         # Add last name only (for family searches)
        #         extra_inputs.append(last)
        #     # Always add the disambiguated variants (they help too)
        #     disambiguated = [f"{full_name} ({a['title']})" for a in char['anime_list'][:3]]
        #     # If full_name already starts with common given name, no harm in duplicates
        #     all_inputs = [full_name] + extra_inputs + disambiguated

        #     actions.append({
        #         "_index": self.indices['search_suggestions'],
        #         "_id": f"character_{char['character_id']}",
        #         "_source": {
        #             "type": "character",
        #             "mal_id": char['character_id'],
        #             "name": char['character_name'],
        #             "image_url": char.get("image_url"),
        #             "suggest": {
        #                 "input": [
        #                     char['character_name'],
        #                     *[f"{char['character_name']} ({a['title']})" for a in char['anime_list'][:3]]  # Top 3 anime
        #                 ],
        #                 "weight": min(char['favorites'] // 100, 100),
        #                 "contexts": {"entity_type": ["character", "global"]}
        #             }
        #         }
        #     })

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
                    "name": studio['name'],
                    "suggest": {
                        "input": [studio['name']],
                        "weight": 100,
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
                    "name": genre['name'],
                    "suggest": {
                        "input": [genre['name']],
                        "weight": 100,
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
                    "name": theme['name'],
                    "suggest": {
                        "input": [theme['name']],
                        "weight": 100,
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
                    "name": demographic['name'],
                    "suggest": {
                        "input": [demographic['name']],
                        "weight": 100,
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

    # Change search_across_all to only search anime_index
    def search_anime(self, query, filters=None, size=50):
        """Search only anime with optional filters"""
        if not filters:
            filters = {}

        search_body = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "size": size,
            "sort": [
                {"_score": {"order": "desc"}},
                {"score": {"order": "desc"}},
                {"popularity": {"order": "asc"}}
            ]
        }

        # Add text search
        if query and query.strip():
            search_body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "title_english^2", "synopsis", "character_names"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            search_body["query"]["bool"]["must"].append({"match_all": {}})

        # Add filters...

        response = self.es.search(index=self.indices['anime'], body=search_body)  # ← ONLY anime_index
        return response['hits']['hits']

    def autocomplete(self, prefix, types=None):
        """Autocomplete suggestions"""
        search_body = {
            "suggest": {
                "anime-suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "suggest",
                        "contexts": {
                            "entity_type": types if types else []
                        },
                        "size": 10,
                        "fuzzy": {
                            "fuzziness": 1
                        }
                    }
                }
            }
        }

        try:
            response = self.es.search(
                index=self.indices['search_suggestions'],
                body=search_body
            )
            return response['suggest']['anime-suggest'][0]['options']
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return []

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
            return response['hits']['hits']
        except Exception as e:
            logger.error(f"Error getting studio anime: {e}")
            return []

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
            return response['hits']['hits']
        except Exception as e:
            logger.error(f"Error getting genre anime: {e}")
            return []

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
            return response['hits']['hits']
        except Exception as e:
            logger.error(f"Error getting theme anime: {e}")
            return []

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
            return response['hits']['hits']
        except Exception as e:
            logger.error(f"Error getting demographic anime: {e}")
            return []

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
