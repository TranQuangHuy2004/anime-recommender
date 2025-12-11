-- Simple anime table for initial setup
CREATE TABLE IF NOT EXISTS anime (
    id SERIAL PRIMARY KEY,
    mal_id INTEGER UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_english VARCHAR(500),
    synopsis TEXT,
    type VARCHAR(50),
    episodes INTEGER,
    score DECIMAL(3,2),
    genres TEXT[],
    members INTEGER,
    popularity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anime_score ON anime(score DESC);
CREATE INDEX IF NOT EXISTS idx_anime_popularity ON anime(popularity);