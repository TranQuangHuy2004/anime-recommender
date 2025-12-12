import json
import os
import glob
import re

# Step 1: Load anime_data.json and extract set of mal_ids
with open('data/anime_data.json', 'r', encoding='utf-8') as f:
    anime_data = json.load(f)

anime_mal_ids = {anime['mal_id'] for anime in anime_data}
print(f"Total anime entries: {len(anime_mal_ids)}")

# Step 2: Find all *_characters.json files and extract their mal_ids
character_files = glob.glob('data/characters/*_characters.json')
character_mal_ids = set()

for file_path in character_files:
    # Extract mal_id from filename (e.g., "52991_characters.json" -> 52991)
    match = re.match(r'.*?(\d+)_characters\.json$', file_path)
    print(match)
    if match:
        mal_id = int(match.group(1))
        character_mal_ids.add(mal_id)

print(f"Character files found: {len(character_mal_ids)}")

# Step 3: Find missing mal_ids
missing_mal_ids = sorted(anime_mal_ids - character_mal_ids)
print(f"Missing character data for {len(missing_mal_ids)} anime:")

# Step 4: Print missing mal_ids with optional title lookup
for mal_id in missing_mal_ids:
    # Find the anime title for context (optional)
    anime = next((a for a in anime_data if a['mal_id'] == mal_id), None)
    title = anime['title'] if anime else 'Unknown'
    print(f"  - MAL ID: {mal_id} (Title: {title})")

# Optional: Save missing list to a file for later use
# if missing_mal_ids:
#     with open('missing_characters.json', 'w') as f:
#         json.dump(list(missing_mal_ids), f, indent=2)
#     print("\nMissing MAL IDs saved to 'missing_characters.json'")
