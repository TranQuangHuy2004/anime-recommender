# 🎌 Anime Recommender System

A **full-stack anime recommendation and search application** built with **Streamlit**, **PostgreSQL**, and **Elasticsearch**, using data fetched from the **[Jikan API](https://jikan.moe/) ([MyAnimeList](https://myanimelist.net/))**.

This project demonstrates:

* Data ingestion & processing pipelines
* Full-text search with Elasticsearch
* Relational storage with PostgreSQL
* A modern Streamlit UI
* **Fully Dockerized local deployment**

> ⚠️ No local Python or database setup required — Docker handles everything.

---

## Features

* 🔍 Fast anime search with Elasticsearch
* 🎭 Detailed anime information (genres, score, synopsis, characters)
* 🧱 Structured relational storage using PostgreSQL
* 🔄 Re-runnable data pipeline (fetch → load → index)
* 🐳 Fully Dockerized
* 📊 Streamlit interactive frontend

---

## Tech Stack

| Layer            | Technology              |
| ---------------- | ----------------------- |
| Frontend         | Streamlit               |
| Backend          | Python                  |
| Database         | PostgreSQL 15           |
| Search Engine    | Elasticsearch 8         |
| Data Source      | Jikan API (MyAnimeList) |
| Containerization | Docker & Docker Compose |

---

## Prerequisites

Make sure you have the following installed:

* **Docker** (v20+)
* **Docker Compose** (v2+)

Check:

```bash
docker --version
docker compose version
```

---

## Local Deployment (Step-by-Step)

### 1. Clone the repository

```bash
git clone https://github.com/TranQuangHuy2004/anime-recommender.git
cd anime-recommender
```

---

### 2. Create environment variables

Copy the example env file:

```bash
cp .env.example .env
```

> You can keep the default values for local development.

---

### 3. Build & start all services

This starts:

* PostgreSQL
* Elasticsearch
* Streamlit app

```bash
docker compose up -d --build
```

Check service status:

```bash
docker compose ps
```

All services should be **running / healthy**.


#### ⏱️ First-Time Setup Time

**Important: The first run may take several minutes.**

- First build (fresh machine): ~5–10 minutes
(Pulling PostgresSQL image + Elasticsearch image +  Python image build + installing dependencies)

- Subsequent runs: ~10–30 seconds (Docker cache reused)

This is normal and happens only once.

---

## Data Pipeline (Required First-Time Setup)

The application requires anime data before it can be used.

### 4. Fetch anime data from Jikan API (Optional)

Do this if you want more anime data, right now there are 3002 animes with characters available in the repo.

```bash
docker compose run --rm app python -m scripts.fetch_anime
```

Optional arguments:

```bash
--limit 100        # Fetch only N anime
--page 1           # Start from page
--continue         # Append to existing data
--mal_ids 1 20     # Fetch specific characters info for anime with   MAL IDs
--check            # Check for duplicated anime and missing character files
```

Example:

```bash
docker compose run --rm app python -m scripts.fetch_anime --continue --limit 1000 --page 121
```

This will continue fetching 1000 anime with characters starting from page 121 (Jikan API only fetch 25 anime per page) and extend the existing data.

---

### 5. Load data into PostgreSQL

```bash
docker compose run --rm app python -m scripts.load_anime
```

This:

* Processes fetched data
* Inserts it into PostgreSQL tables

---

### 6. Index data into Elasticsearch

```bash
docker compose run --rm app python -m scripts.index_anime
```

This creates:

* `anime_index`
* `search_suggestion_index`

---

## Access the Application

Once indexing is complete, open your browser:

```
http://localhost:8501
```

🎉 You should now see the **Anime Recommender App** running!

---

## Updating Data (Re-run Anytime)

To update the dataset:

```bash
docker compose run --rm app python -m scripts.fetch_anime
docker compose run --rm app python -m scripts.load_anime
docker compose run --rm app python -m scripts.index_anime
```

The Streamlit app will reflect new data automatically
(refresh page or clear cache if needed).

---

## Stop & Clean Up

Stop all containers:

```bash
docker compose down
```

Remove containers **and volumes** (reset database & index):

```bash
docker compose down -v
```

---

## Project Structure

```text
anime-recommender/
├── app.py                 # Streamlit frontend
├── scripts/               # Data pipeline scripts
│   ├── fetch_anime.py
│   ├── load_anime.py
│   └── index_anime.py
├── init-scripts/          # PostgreSQL schema
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Future Improvements

* Vector similarity search (FAISS)
* Recommendation ranking
* User personalization
* Caching optimization
* Cloud deployment

---

## License

This project is for **educational purpose**.
