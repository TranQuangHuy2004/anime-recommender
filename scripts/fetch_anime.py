import requests
import time
from services.database import Database
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class AnimeFetcher:
    def __init__(self):
        self.base_url = os.getenv("JIKAN_BASE_URL", "https://api.jikan.moe/v4")
        self.db = Database()
        self.delay = 0.5  # Delay between requests to respect rate limit

    def fetch_top_anime(self, limit=100):
        """Fetch top anime from MyAnimeList"""
        all_anime = []
        page = 1

        print(f"Fetching top {limit} anime from MyAnimeList...")

        with tqdm(total=limit) as pbar:
            while len(all_anime) < limit:
                try:
                    # Fetch a page of anime
                    response = requests.get(
                        f"{self.base_url}/top/anime",
                        params={"page": page, "limit": 25}
                    )
                    response.raise_for_status()

                    data = response.json()
                    anime_list = data.get('data', [])

                    if not anime_list:
                        break

                    # Process each anime
                    for anime in anime_list:
                        if len(all_anime) >= limit:
                            break

                        anime_data = self.extract_anime_data(anime)
                        all_anime.append(anime_data)
                        pbar.update(1)

                        # Insert into database
                        self.db.insert_anime(anime_data)

                    page += 1
                    time.sleep(self.delay)  # Rate limiting

                except Exception as e:
                    print(f"Error fetching page {page}: {e}")
                    break

        print(f"✅ Successfully fetched {len(all_anime)} anime")
        return all_anime

    def extract_anime_data(self, anime):
        """Extract relevant fields from API response"""
        return {
            'mal_id': anime['mal_id'],
            'title': anime['title'],
            'title_english': anime.get('title_english'),
            'synopsis': anime.get('synopsis', ''),
            'type': anime.get('type'),
            'episodes': anime.get('episodes'),
            'score': anime.get('score'),
            'genres': anime.get('genres', []),
            'members': anime.get('members'),
            'popularity': anime.get('popularity')
        }


if __name__ == "__main__":
    fetcher = AnimeFetcher()

    # Fetch a small batch for testing
    limit = int(os.getenv("MAX_ANIME", 50))
    anime_data = fetcher.fetch_top_anime(limit=limit)

    # Save to JSON for backup
    import json
    with open('data/anime_data.json', 'w', encoding='utf-8') as f:
        json.dump(anime_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Data saved to data/anime_data.json")
