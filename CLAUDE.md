# VIBE — Istanbul Event Discovery App

## Architecture Overview

```
vibe/
├── backend/          # Python + FastAPI + SQLite + APScheduler
│   ├── main.py       # FastAPI app, all REST routes
│   ├── db.py         # SQLite connection, schema init, helpers
│   ├── models.py     # Pydantic request/response models
│   ├── recommendations.py  # Genre+venue based recommendation engine
│   ├── scheduler.py  # APScheduler — runs all scrapers every 6h
│   └── scrapers/     # One file per source, each exports scrape()
└── frontend/         # React + Vite + Tailwind CSS
    └── src/
        ├── App.jsx         # Root component, state management
        ├── api.js          # All fetch calls to backend
        └── components/
            ├── EventCard.jsx    # Event card with like button
            ├── GenreFilter.jsx  # Multi-select genre pills
            ├── UserSwitcher.jsx # User dropdown (max 10)
            └── TabBar.jsx       # "For You" / "All Events" tabs
```

## Backend

### Database (SQLite — vibe.db)
- **events**: id, title, venue, date, genres (JSON array), city, ticket_url, image_url, source_url, source, created_at
- **users**: id, username, created_at (max 10 users, no passwords)
- **likes**: user_id, event_id, created_at (unique per pair)
- **scraper_logs**: source, status, message, events_found, created_at

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /events | List events (filters: genre, city, date_from, date_to, venue, user_id) |
| POST | /events/{id}/like | Like an event |
| DELETE | /events/{id}/like | Unlike an event |
| GET | /recommendations/{user_id} | Personalized recommendations |
| GET | /users | List all users |
| POST | /users | Create user (max 10) |
| GET | /scraper/run | Manually trigger all scrapers |
| GET | /scraper/logs | Recent scraper logs |
| GET | /scraper/status | Last run time + event count |

### Scrapers
Each scraper in `backend/scrapers/` exports a `scrape() -> list[dict]` function.

Event dict shape:
```python
{
    "title": str,
    "venue": str,
    "date": str,           # ISO format: "2024-03-15" or "2024-03-15T20:00"
    "genres": list[str],   # from genre_keywords or inferred
    "city": "Istanbul",
    "ticket_url": str,
    "image_url": str,
    "source_url": str,
}
```

**Important scraper notes:**
- Many Turkish sites use JavaScript rendering (React SPAs). BeautifulSoup alone won't work for those.
- If a site blocks scraping, the scraper will raise an exception which the scheduler catches and logs.
- Scrapers run every 6 hours. Errors in one scraper do NOT stop others.
- For JS-rendered sites, consider upgrading to Playwright later.

### Recommendation Engine
- Analyzes all events the user has liked
- Counts genre frequencies and venue frequencies
- Scores remaining events: genre_match × 0.7 + venue_match × 0.3
- Returns top N events sorted by score (then date)
- If a user has 3+ likes for a genre, that genre dominates recommendations

## Frontend

### Design System
- **Dark nightlife aesthetic** — near-black backgrounds, neon purple/pink accents
- Background: `#080810`, Cards: `#12121e`, Borders: `#1e1e30`
- Accent: purple `#7c3aed`, pink `#ec4899`
- No light mode

### Genre Tags Available
`electronic`, `techno`, `house`, `deep-house`, `ambient`, `rock`, `metal`, `alternative`, `indie`, `jazz`, `classical`, `pop`, `hip-hop`, `world-music`, `festival`, `dj-set`, `live`, `acoustic`

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Backend runs on http://localhost:8000
Frontend runs on http://localhost:5173
API docs at http://localhost:8000/docs

## Adding a New Scraper

1. Create `backend/scrapers/mysource.py`
2. Export a `scrape() -> list[dict]` function
3. The scheduler auto-discovers all `.py` files in the scrapers directory
4. No registration needed — it just works
