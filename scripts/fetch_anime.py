import requests
import time
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class AnimeFetcher:
    '''
    Fetch and Save Anime as JSON
    '''

    def __init__(self, continue_fetching=False, start_page=1):
        self.base_url = os.getenv("JIKAN_BASE_URL", "https://api.jikan.moe/v4")
        self.delay = 0.5  # Rate limiting delay
        self.continue_fetching = continue_fetching
        self.start_page = start_page

        # Create data directories
        self.data_dir = Path("data")
        self.anime_dir = self.data_dir
        self.characters_dir = self.data_dir / "characters"

        self.anime_dir.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(parents=True, exist_ok=True)

    def save_anime_json(self, anime_data, continue_fetching=False):
        """Save anime data as JSON file"""
        filename = self.anime_dir / "anime_data.json"

        if continue_fetching and filename.exists():
            # Load existing data and append new data
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

                if anime_data:
                    existing_data.extend(anime_data)
                    anime_data = existing_data
                    print(f"✅ Appended {len(anime_data)} new anime to existing file")
                else:
                    print("⚠️  No new anime to append")
                    return filename

            except json.JSONDecodeError as e:
                print(f"⚠️  Error reading existing JSON file: {e}. Creating new file.")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(anime_data, f, ensure_ascii=False, indent=2)
        return filename

    def save_characters_json(self, mal_id, characters_data):
        """Save characters data as JSON file"""
        filename = self.characters_dir / f"{mal_id}_characters.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(characters_data, f, ensure_ascii=False, indent=2)
        return filename

    def load_anime_json(self):
        """Load anime data from JSON file"""
        filename = self.anime_dir / "anime_data.json"
        if filename.exists():
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def load_characters_json(self, mal_id):
        """Load characters data from JSON file"""
        filename = self.characters_dir / f"{mal_id}_characters.json"
        if filename.exists():
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_existing_mal_ids(self):
        """Get set of MAL IDs already in the JSON file"""
        existing_data = self.load_anime_json()
        return {anime['mal_id'] for anime in existing_data}

    def fetch_extract_anime_characters(self, mal_id):
        """Fetch and extract anime characters, then save to JSON file"""
        try:
            # Fetch characters
            characters_response = requests.get(
                f"{self.base_url}/anime/{mal_id}/characters",
                timeout=10
            )
            # If rate limited, wait and retry
            if characters_response.status_code == 429:
                print(f"Rate limited for {mal_id}, waiting 60 seconds...")
                time.sleep(60)
                characters_response = requests.get(
                    f"{self.base_url}/anime/{mal_id}/characters",
                    timeout=10
                )

            characters_data = []
            if characters_response.status_code == 200:
                characters_data = characters_response.json()['data']

            for char in characters_data:
                if "voice_actors" in char:
                    char["voice_actors"] = [
                        va for va in char["voice_actors"]
                        if va.get("language", "").lower().strip() == "japanese"
                    ]

            self.save_characters_json(mal_id, characters_data)
            return characters_data

        except Exception as e:
            print(f"Error fetching characters for anime {mal_id}: {e}")
            return None

    def extract_anime_data(self, anime):
        """Extract all anime fields from API response"""
        # Handle trailer
        trailer_url = None
        if anime.get('trailer') and anime['trailer'].get('embed_url'):
            trailer_url = anime['trailer']['embed_url']

        # Handle aired string
        aired_string = None
        if anime.get('aired') and anime['aired'].get('string'):
            aired_string = anime['aired']['string']

        return {
            'mal_id': anime['mal_id'],
            'image_url': anime['images']['webp']['large_image_url'] if anime.get('images', {}).get('webp', {}).get('large_image_url') else anime['images']['jpg']['image_url'],
            'trailer_url': trailer_url,
            'title': anime['title'],
            'title_english': anime.get('title_english'),
            'title_japanese': anime.get('title_japanese'),
            'title_synonyms': anime.get('title_synonyms', []),
            'synopsis': anime.get('synopsis', ''),
            'type': anime.get('type'),
            'source': anime.get('source'),
            'episodes': anime.get('episodes'),
            'status': anime.get('status'),
            'aired': aired_string,
            'duration': anime.get('duration'),
            'rating': anime.get('rating'),
            'score': anime.get('score'),
            'popularity': anime.get('popularity'),
            'season': anime.get('season'),
            'year': anime.get('year'),
            'studios': [{'mal_id': s['mal_id'], 'name': s['name']} for s in anime.get('studios', [])],
            'genres': [{'mal_id': g['mal_id'], 'name': g['name']} for g in anime.get('genres', [])],
            'themes': [{'mal_id': t['mal_id'], 'name': t['name']} for t in anime.get('themes', [])],
            'demographics': [{'mal_id': d['mal_id'], 'name': d['name']} for d in anime.get('demographics', [])]
        }

    def fetch_top_anime_with_characters(self, limit=None):
        """Fetch top anime with full details and characters and save them as JSON files"""
        print(f"Fetching top {limit} anime with full details...")

        # First, get list of top anime IDs
        anime_data = []
        page = self.start_page
        total_fetched = 0

        # Get existing MAL IDs to avoid duplicates
        existing_ids = self.get_existing_mal_ids()
        print(f"Found {len(existing_ids)} existing anime in database")

        # print("Getting anime IDs...")
        with tqdm(total=limit, desc="Fetching anime") as pbar:
            while limit and total_fetched < limit:
                try:
                    response = requests.get(
                        f"{self.base_url}/top/anime",
                        params={"page": page, "limit": 25}
                    )
                    response.raise_for_status()

                    data = response.json()
                    for anime in data.get('data', []):
                        if total_fetched >= limit:
                            break
                        new_anime = self.extract_anime_data(anime)
                        if not new_anime['mal_id'] in existing_ids:
                            anime_data.append(new_anime)
                            total_fetched += 1

                        pbar.update(1)

                    page += 1
                    time.sleep(self.delay)

                except Exception as e:
                    print(f"Error fetching anime list page {page}: {e}")
                    break

        print(f"✅ Successfully fetched top {len(anime_data)} anime")
        self.save_anime_json(anime_data, continue_fetching=self.continue_fetching)

        # Now fetch characters for each anime
        print(f"\nFetching characters info for {len(anime_data)} anime...")
        successful_chars = 0
        error_anime_id = []

        with tqdm(total=len(anime_data), desc="Fetching anime characters") as pbar:
            for anime in anime_data:
                try:
                    # Fetch anime details and characters
                    mal_id = anime['mal_id']
                    characters_data = self.fetch_extract_anime_characters(mal_id)

                    if characters_data:
                        successful_chars += 1
                    else:
                        error_anime_id.append(mal_id)

                    # time.sleep(self.delay)
                    pbar.update(1)

                except Exception as e:
                    print(f"\nError processing characters for anime {mal_id}: {e}")
                    pbar.update(1)
                    continue

        print(f"\n✅ Successfully fetched characters for {successful_chars} anime.")
        return len(anime_data), successful_chars, error_anime_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Anime Data Fetcher")
    parser.add_argument('--mal_ids', nargs="*", type=int, default=None,
                        help='List of MAL IDs to fetch characters for (e.g., --mal_ids 1 20 30276). If omitted, fetch normally.')
    parser.add_argument('--page', type=int, default=1,
                        help='Page number to start fetching from (default: 1)')
    parser.add_argument('--continue', dest='continue_fetch', action='store_true',
                        help='Continue fetching and append to existing anime_data.json')
    parser.add_argument('--limit', type=int, default=None,
                        help='Total number of anime to fetch (default: None = fetch all pages)')
    args = parser.parse_args()

    fetcher = AnimeFetcher(
        continue_fetching=args.continue_fetch,
        start_page=args.page
    )

    print("=" * 50)
    print("FETCHING DATA FROM JIKAN API")
    print("=" * 50)

    if args.mal_ids:
        # User gave specific mal_ids → fetch only these
        print(f"\nFetching characters for MAL IDs: {args.mal_ids}")
        for id in args.mal_ids:
            fetcher.fetch_extract_anime_characters(id)
    else:
        # Normal full fetching
        print(f"\nFetching from page {args.page}")
        anime_count, char_count, error_anime_id = fetcher.fetch_top_anime_with_characters(limit=args.limit)
        print(f"\nFetched: {anime_count} anime, {char_count} with characters")
        print(f"Anime that couldn't fetch characters: {error_anime_id}")
