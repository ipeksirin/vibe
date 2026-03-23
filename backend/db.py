import sqlite3
import json
import os
from contextlib import contextmanager

_DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(_DATA_DIR, "vibe.db")


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                venue TEXT,
                date TEXT,
                genres TEXT DEFAULT '[]',
                city TEXT DEFAULT 'Istanbul',
                ticket_url TEXT,
                image_url TEXT,
                source_url TEXT,
                source TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                UNIQUE(user_id, event_id)
            );

            CREATE TABLE IF NOT EXISTS scraper_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                events_found INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
            CREATE INDEX IF NOT EXISTS idx_events_venue ON events(venue);
            CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique ON events(title, date);
            CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id);
            CREATE INDEX IF NOT EXISTS idx_likes_event ON likes(event_id);
        """)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    if "genres" in d and isinstance(d["genres"], str):
        try:
            d["genres"] = json.loads(d["genres"])
        except Exception:
            d["genres"] = []
    return d


VENUE_ALIASES = {
    "zorlu": "Zorlu PSM",
}


def normalize_venue(venue: str) -> str:
    if not venue:
        return venue
    lower = venue.lower()
    for keyword, canonical in VENUE_ALIASES.items():
        if keyword in lower:
            return canonical
    return venue


def upsert_event(conn, event: dict, source: str) -> bool:
    """Insert event, skip if duplicate (same title+venue+date or same source_url). Returns True if inserted."""
    import json as _json

    event = {**event, "venue": normalize_venue(event.get("venue", ""))}
    genres_json = _json.dumps(event.get("genres", []))

    # Dedup by source_url if available
    if event.get("source_url"):
        existing = conn.execute(
            "SELECT id FROM events WHERE source_url = ?", (event["source_url"],)
        ).fetchone()
        if existing:
            return False

    # Dedup by title+venue+date
    if event.get("title") and event.get("venue") and event.get("date"):
        existing = conn.execute(
            "SELECT id FROM events WHERE title = ? AND venue = ? AND date = ?",
            (event["title"], event["venue"], event["date"]),
        ).fetchone()
        if existing:
            return False

    conn.execute(
        """
        INSERT INTO events (title, venue, date, genres, city, ticket_url, image_url, source_url, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.get("title", ""),
            event.get("venue", ""),
            event.get("date", ""),
            genres_json,
            event.get("city", "Istanbul"),
            event.get("ticket_url", ""),
            event.get("image_url", ""),
            event.get("source_url", ""),
            source,
        ),
    )
    return True
