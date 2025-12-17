-- Main anime table
CREATE TABLE IF NOT EXISTS anime (
    mal_id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    title_english VARCHAR(500),
    title_japanese VARCHAR(500),
    title_synonyms TEXT[],
    type VARCHAR(50),
    source VARCHAR(100),
    episodes INTEGER,
    status VARCHAR(50),
    aired_string VARCHAR(200),
    duration VARCHAR(50),
    rating VARCHAR(50),
    score DECIMAL(3,2),
    popularity INTEGER,
    season VARCHAR(50),
    year INTEGER,
    synopsis TEXT,
    image_url VARCHAR(500),
    trailer_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Studios table
CREATE TABLE IF NOT EXISTS studios (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anime-Studio junction table (many-to-many)
CREATE TABLE IF NOT EXISTS anime_studios (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    studio_id INTEGER REFERENCES studios(mal_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, studio_id)
);

-- Genres table
CREATE TABLE IF NOT EXISTS genres (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anime-Genre junction table
CREATE TABLE IF NOT EXISTS anime_genres (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(mal_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, genre_id)
);

-- Themes table
CREATE TABLE IF NOT EXISTS themes (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anime-Theme junction table
CREATE TABLE IF NOT EXISTS anime_themes (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    theme_id INTEGER REFERENCES themes(mal_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, theme_id)
);

-- Demographics table
CREATE TABLE IF NOT EXISTS demographics (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anime-Demographic junction table
CREATE TABLE IF NOT EXISTS anime_demographics (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    demographic_id INTEGER REFERENCES demographics(mal_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, demographic_id)
);

-- Characters table
CREATE TABLE IF NOT EXISTS characters (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    image_url VARCHAR(500),
    favorites INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Actors table (Japanese only)
CREATE TABLE IF NOT EXISTS voice_actors (
    mal_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    image_url VARCHAR(500),
    language VARCHAR(50) DEFAULT 'Japanese',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anime-Character-VoiceActor junction table
CREATE TABLE IF NOT EXISTS anime_characters (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES characters(mal_id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, character_id)
);

CREATE TABLE IF NOT EXISTS anime_character_voice_actors (
    anime_id INTEGER REFERENCES anime(mal_id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES characters(mal_id) ON DELETE CASCADE,
    voice_actor_id INTEGER REFERENCES voice_actors(mal_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anime_id, character_id, voice_actor_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_anime_studios_anime_id ON anime_studios(anime_id);
CREATE INDEX IF NOT EXISTS idx_anime_studios_studio_id ON anime_studios(studio_id);

CREATE INDEX IF NOT EXISTS idx_anime_genres_anime_id ON anime_genres(anime_id);
CREATE INDEX IF NOT EXISTS idx_anime_genres_genre_id ON anime_genres(genre_id);

CREATE INDEX IF NOT EXISTS idx_anime_themes_anime_id ON anime_themes(anime_id);
CREATE INDEX IF NOT EXISTS idx_anime_themes_theme_id ON anime_themes(theme_id);

CREATE INDEX IF NOT EXISTS idx_anime_demographics_anime_id ON anime_demographics(anime_id);
CREATE INDEX IF NOT EXISTS idx_anime_demographics_demographic_id ON anime_demographics(demographic_id);

CREATE INDEX IF NOT EXISTS idx_anime_characters_anime_id ON anime_characters(anime_id);

CREATE INDEX IF NOT EXISTS idx_characters_favorites_desc ON characters(favorites DESC);

CREATE INDEX IF NOT EXISTS idx_acva_anime_id ON anime_character_voice_actors (anime_id);
CREATE INDEX IF NOT EXISTS idx_acva_character_id ON anime_character_voice_actors (character_id);
CREATE INDEX IF NOT EXISTS idx_acva_voice_actor_id ON anime_character_voice_actors (voice_actor_id);

-- CREATE INDEX IF NOT EXISTS idx_anime_score ON anime(score DESC);
-- CREATE INDEX IF NOT EXISTS idx_anime_popularity ON anime(popularity);
-- CREATE INDEX IF NOT EXISTS idx_anime_type ON anime(type);
-- CREATE INDEX IF NOT EXISTS idx_anime_season_year ON anime(year, season);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for anime table
CREATE TRIGGER update_anime_updated_at BEFORE UPDATE ON anime
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();