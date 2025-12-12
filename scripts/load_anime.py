from tqdm import tqdm
from services.database import Database
from scripts.fetch_anime import AnimeFetcher


class AnimeLoader:
    """
    This class helps building staging lists to speed up the insert to database
    """

    def __init__(self):
        self.db = Database()
        self.fetcher = AnimeFetcher()

        # Staging lists
        self.anime_rows = []
        self.studio_rows = []
        self.genre_rows = []
        self.theme_rows = []
        self.demographic_rows = []

        self.anime_studios = []
        self.anime_genres = []
        self.anime_themes = []
        self.anime_demographics = []

        self.character_rows = []
        self.voice_actor_rows = []
        self.anime_characters_voice_actors = []

    def build_staging_lists(self):
        print("\nBuilding staging lists...")

        anime_list = self.fetcher.load_anime_json()

        for anime in tqdm(anime_list, desc="Anime metadata", ncols=80):
            mal_id = anime['mal_id']

            # ----------- Anime row -------------
            self.anime_rows.append((
                mal_id,
                anime['title'],
                anime.get('title_english'),
                anime.get('title_japanese'),
                anime.get('title_synonyms', []),
                anime.get('type'),
                anime.get('source'),
                anime.get('episodes'),
                anime.get('status'),
                anime.get('aired'),
                anime.get('duration'),
                anime.get('rating'),
                anime.get('score'),
                anime.get('popularity'),
                anime.get('season'),
                anime.get('year'),
                anime.get('synopsis', ''),
                anime.get('image_url'),
                anime.get('trailer_url')
            ))

            # ----------- Studios ---------------
            for studio in anime.get('studios', []):
                self.studio_rows.append((studio['mal_id'], studio['name']))
                self.anime_studios.append((mal_id, studio['mal_id']))

            # ----------- Genres ----------------
            for genre in anime.get('genres', []):
                self.genre_rows.append((genre['mal_id'], genre['name']))
                self.anime_genres.append((mal_id, genre['mal_id']))

            # ----------- Themes ----------------
            for theme in anime.get('themes', []):
                self.theme_rows.append((theme['mal_id'], theme['name']))
                self.anime_themes.append((mal_id, theme['mal_id']))

            # ----------- Demographics ----------
            for d in anime.get('demographics', []):
                self.demographic_rows.append((d['mal_id'], d['name']))
                self.anime_demographics.append((mal_id, d['mal_id']))

            # ----------- Characters ---------------
            character_list = self.fetcher.load_characters_json(mal_id)
            for entry in character_list:
                char = entry['character']

                # character main table
                self.character_rows.append((
                    char['mal_id'],
                    char['name'],
                    char['images']['webp']['image_url'] if char.get('images', {}).get('webp', {}).get('image_url', {}) else char['images']['jpg']['image_url'],
                    entry.get('role'),
                    entry.get('favorites')
                ))

                # voice actor table
                vas = [
                    va for va in entry['voice_actors']
                    if va['language'] == 'Japanese'
                ]
                for va in vas:
                    person = va['person']

                    self.voice_actor_rows.append((
                        person['mal_id'],
                        person['name'],
                        person['images']['jpg']['image_url'],
                        'Japanese'
                    ))

                    # anime-character-voiceactor junction
                    self.anime_characters_voice_actors.append((
                        mal_id,
                        char['mal_id'],
                        person['mal_id']
                    ))

        self.character_rows = self.dedupe_rows(self.character_rows, key_index=0)
        self.voice_actor_rows = self.dedupe_rows(self.voice_actor_rows, key_index=0)

        print("✅ Building staging lists completed.")

    def bulk_insert(self):
        print("\nBulk inserting into database...")

        self.db.bulk_insert_anime(self.anime_rows)

        self.db.bulk_insert_studios(self.studio_rows)
        self.db.bulk_link_anime_studios(self.anime_studios)

        self.db.bulk_insert_categories('genres', self.genre_rows)
        self.db.bulk_link_anime_categories('anime_genres', self.anime_genres)

        self.db.bulk_insert_categories('themes', self.theme_rows)
        self.db.bulk_link_anime_categories('anime_themes', self.anime_themes)

        self.db.bulk_insert_categories('demographics', self.demographic_rows)
        self.db.bulk_link_anime_categories('anime_demographics', self.anime_demographics)

        self.db.bulk_insert_characters(self.character_rows)
        self.db.bulk_insert_voice_actors(self.voice_actor_rows)
        self.db.bulk_link_anime_characters_voice_actors(self.anime_characters_voice_actors)

        print("✅ Bulk insert completed.")

    def dedupe_rows(self, rows, key_index=0):
        seen = {}
        for r in rows:
            seen[r[key_index]] = r   # last one wins
        return list(seen.values())

    def run(self):
        self.build_staging_lists()
        print(self.character_rows[0])
        self.bulk_insert()


if __name__ == "__main__":
    loader = AnimeLoader()
    loader.run()
