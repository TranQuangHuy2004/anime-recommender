import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
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

    def insert_anime(self, anime_data):
        """Insert single anime record"""
        query = """
        INSERT INTO anime 
        (mal_id, title, title_english, synopsis, type, episodes, score, genres, members, popularity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (mal_id) DO NOTHING
        """

        genres = [g['name'] for g in anime_data.get('genres', [])] if anime_data.get('genres') else []

        params = (
            anime_data['mal_id'],
            anime_data['title'],
            anime_data.get('title_english'),
            anime_data.get('synopsis', ''),
            anime_data.get('type'),
            anime_data.get('episodes'),
            anime_data.get('score'),
            genres,
            anime_data.get('members'),
            anime_data.get('popularity')
        )

        return self.execute_query(query, params)
