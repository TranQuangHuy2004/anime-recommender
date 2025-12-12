import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

CATEGORY_COLUMN_MAP = {
    "anime_genres": "genre_id",
    "anime_themes": "theme_id",
    "anime_demographics": "demographic_id",
}


class Database:
    """
    Ways to execute SQL query
    """

    def __init__(self):
        self.conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "anime_db"),
            "user": os.getenv("DB_USER", "anime_user"),
            "password": os.getenv("DB_PASSWORD", "anime_password")
        }
        self.test_connection()

    def test_connection(self):
        """Test database connection"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            print("✅ PostgreSQL connection successful!")
            conn.close()
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection"""
        conn = psycopg2.connect(**self.conn_params, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if query.strip().upper().startswith("SELECT"):
                    return cur.fetchall()
                return cur.rowcount

    # ========== ANIME METHODS ==========

    def insert_anime(self, anime_data):
        """Insert or update anime with all details"""
        query = """
        INSERT INTO anime (
            mal_id, title, title_english, title_japanese, title_synonyms, type,
            source, episodes, status, aired_string, duration, rating,
            score, popularity, season, year, synopsis, image_url,
            trailer_url
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, 
            %s
        )
        ON CONFLICT (mal_id) DO UPDATE SET
            title = EXCLUDED.title,
            title_english = EXCLUDED.title_english,
            score = EXCLUDED.score,
            popularity = EXCLUDED.popularity,
            synopsis = EXCLUDED.synopsis,
            image_url = EXCLUDED.image_url,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """

        # Handle None values for trailer
        trailer_url = None
        if anime_data.get('trailer_url'):
            trailer_url = anime_data['trailer_url']

        params = (
            anime_data['mal_id'],
            anime_data['title'],
            anime_data.get('title_english'),
            anime_data.get('title_japanese'),
            anime_data.get('title_synonyms', []),
            anime_data.get('type'),
            anime_data.get('source'),
            anime_data.get('episodes'),
            anime_data.get('status'),
            anime_data.get('aired'),
            anime_data.get('duration'),
            anime_data.get('rating'),
            anime_data.get('score'),
            anime_data.get('popularity'),
            anime_data.get('season'),
            anime_data.get('year'),
            anime_data.get('synopsis', ''),
            anime_data.get('image_url'),
            trailer_url
        )

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                return result['id'] if result else None

    def bulk_insert_anime(self, anime_rows):
        """
        Insert or update MANY anime rows at once using execute_values

        :param anime_rows: list of tuples
        """

        query = """
        INSERT INTO anime (
            mal_id, title, title_english, title_japanese, title_synonyms, type,
            source, episodes, status, aired_string, duration, rating,
            score, popularity, season, year, synopsis, image_url, trailer_url
        ) VALUES %s
        ON CONFLICT (mal_id) DO UPDATE SET
            title = EXCLUDED.title,
            title_english = EXCLUDED.title_english,
            score = EXCLUDED.score,
            popularity = EXCLUDED.popularity,
            synopsis = EXCLUDED.synopsis,
            image_url = EXCLUDED.image_url,
            updated_at = CURRENT_TIMESTAMP
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, anime_rows)

    # ========== STUDIO METHODS ==========

    def insert_studio(self, studio_data):
        query = """
        INSERT INTO studios (mal_id, name)
        VALUES (%s, %s)
        ON CONFLICT (mal_id) DO NOTHING
        RETURNING id
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    studio_data['mal_id'],
                    studio_data['name']
                ))
                result = cur.fetchone()
                return result['id'] if result else None

    def link_anime_studio(self, anime_id, studio_id):
        query = """
        INSERT INTO anime_studios (anime_id, studio_id)
        VALUES (%s, %s)
        ON CONFLICT (anime_id, studio_id) DO NOTHING
        """
        self.execute_query(query, (anime_id, studio_id))

    def bulk_insert_studios(self, studio_rows):
        """
        Insert or update MANY studio rows at once using execute_values

        :param studio_rows: list of tuples
        """
        query = """
        INSERT INTO studios (mal_id, name)
        VALUES %s
        ON CONFLICT (mal_id) DO NOTHING
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, studio_rows)

    def bulk_link_anime_studios(self, anime_studios):
        """
        Insert or update MANY anime_studios rows at once using execute_values

        :param anime_studios: list of tuples
        """
        query = """
        INSERT INTO anime_studios (anime_id, studio_id)
        VALUES %s
        ON CONFLICT (anime_id, studio_id) DO NOTHING
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, anime_studios)

    # ========== GENRE/THEME/DEMOGRAPHIC METHODS ==========

    def insert_category(self, table_name, category_data):
        """Generic method for genres, themes, demographics"""
        query = f"""
        INSERT INTO {table_name} (mal_id, name)
        VALUES (%s, %s)
        ON CONFLICT (mal_id) DO NOTHING
        RETURNING id
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    category_data['mal_id'],
                    category_data['name']
                ))
                result = cur.fetchone()
                return result['id'] if result else None

    def link_anime_categor(self, junction_table, anime_id, category_id):
        query = f"""
        INSERT INTO {junction_table} (anime_id, {CATEGORY_COLUMN_MAP[junction_table]})
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """
        self.execute_query(query, (anime_id, category_id))

    def bulk_insert_categories(self, table_name, category_rows):
        """
        Generic bulk insert of update method for genres, themes, demographics

        :param table_name: genres/themes/demographics
        :param category_rows: list of tuples
        """

        query = f"""
        INSERT INTO {table_name} (mal_id, name)
        VALUES %s
        ON CONFLICT (mal_id) DO NOTHING
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, category_rows)

    def bulk_link_anime_categories(self, junction_table, anime_categories):
        """
        Insert or update MANY anime_categories rows at once using execute_values

        :param junction_table: name of the junction table
        :param anime_categories: list of tuples
        """
        query = f"""
        INSERT INTO {junction_table} (anime_id, {CATEGORY_COLUMN_MAP[junction_table]})
        VALUES %s
        ON CONFLICT DO NOTHING
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, anime_categories)

    # ========== CHARACTER METHODS ==========

    def insert_character(self, character_data):
        query = """
        INSERT INTO characters (mal_id, name, image_url, role, favorites)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (mal_id) DO UPDATE SET
            name = EXCLUDED.name,
            image_url = EXCLUDED.image_url,
            role = EXCLUDED.role,
            favorites = EXCLUDED.favorites
        RETURNING id
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    character_data['mal_id'],
                    character_data['name'],
                    character_data['image_url'],
                    character_data['role'],
                    character_data['favorites']
                ))
                result = cur.fetchone()
                return result['id'] if result else None

    def bulk_insert_characters(self, character_rows):
        """
        Insert or update MANY character rows at once using execute_values

        :param character_rows: list of tuples
        """

        query = """
        INSERT INTO characters (mal_id, name, image_url, role, favorites)
        VALUES %s
        ON CONFLICT (mal_id) DO UPDATE SET
            name = EXCLUDED.name,
            image_url = EXCLUDED.image_url,
            role = EXCLUDED.role,
            favorites = EXCLUDED.favorites
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, character_rows)

    # ========== VOICE ACTOR METHODS ==========

    def insert_voice_actor(self, voice_actor_data):
        query = """
        INSERT INTO voice_actors (mal_id, name, image_url, language)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (mal_id) DO UPDATE SET
            name = EXCLUDED.name,
            image_url = EXCLUDED.image_url
        RETURNING id
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    voice_actor_data['mal_id'],
                    voice_actor_data['name'],
                    voice_actor_data.get('image_url'),
                    voice_actor_data.get('language', 'Japanese')
                ))
                result = cur.fetchone()
                return result['id'] if result else None

    def bulk_insert_voice_actors(self, voice_actor_rows):
        """
        Insert or update MANY voice actor rows at once using execute_values

        :param voice_actor_rows: list of tuples
        """

        query = """
        INSERT INTO voice_actors (mal_id, name, image_url, language)
        VALUES %s
        ON CONFLICT (mal_id) DO UPDATE SET
            name = EXCLUDED.name,
            image_url = EXCLUDED.image_url
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, voice_actor_rows)

    # ========== ANIME-CHARACTER-VOICE ACTOR LINK ==========

    def link_anime_character_voice(self, anime_id, character_id, voice_actor_id):
        query = """
        INSERT INTO anime_characters (anime_id, character_id, voice_actor_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (anime_id, character_id, voice_actor_id) DO NOTHING
        """
        self.execute_query(query, (anime_id, character_id, voice_actor_id))

    def bulk_link_anime_characters_voice_actors(self, anime_characters_voice_actors):
        """
        Insert or update MANY anime_characters_voice_actors rows at once using execute_values

        :param anime_characters_voice_actors: list of tuples
        """

        query = """
        INSERT INTO anime_characters (anime_id, character_id, voice_actor_id)
        VALUES %s
        ON CONFLICT (anime_id, character_id, voice_actor_id) DO NOTHING
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, anime_characters_voice_actors)
