import logging
import os
import threading
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import get_db, init_db, migrate_normalize_genres, row_to_dict
from models import UserCreate
from recommendations import get_recommendations
from scheduler import run_all_scrapers, start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="VIBE", description="Istanbul Event Discovery")

_extra_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")
_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"] + [o for o in _extra_origins if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    with get_db() as conn:
        updated = migrate_normalize_genres(conn)
        if updated:
            logger.info(f"Genre migration: {updated} events normalized")
    start_scheduler()
    logger.info("VIBE backend ready")


# ─── Events ───────────────────────────────────────────────────────────────────

@router.get("/events")
def list_events(
    genre: Optional[str] = None,
    genres: Optional[str] = None,
    exclude_genres: Optional[str] = None,
    city: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    venue: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = Query(default=60, le=200),
    offset: int = 0,
):
    with get_db() as conn:
        query = "SELECT * FROM events WHERE 1=1"
        params: list = []

        if genres:
            genre_list = [g.strip() for g in genres.split(',') if g.strip()]
            if genre_list:
                placeholders = ' OR '.join(['genres LIKE ?' for _ in genre_list])
                query += f' AND ({placeholders})'
                params.extend([f'%"{g}"%' for g in genre_list])
        elif genre:
            query += ' AND genres LIKE ?'
            params.append(f'%"{genre}"%')

        if exclude_genres:
            for eg in [g.strip() for g in exclude_genres.split(',') if g.strip()]:
                query += ' AND genres NOT LIKE ?'
                params.append(f'%"{eg}"%')

        if city:
            query += " AND city = ?"
            params.append(city)
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if venue:
            query += " AND venue LIKE ?"
            params.append(f"%{venue}%")

        query += " ORDER BY date ASC LIMIT ? OFFSET ?"
        params += [limit, offset]

        rows = conn.execute(query, params).fetchall()
        events = [row_to_dict(r) for r in rows]

        if user_id:
            liked_ids = {
                r[0]
                for r in conn.execute(
                    "SELECT event_id FROM likes WHERE user_id = ?", (user_id,)
                ).fetchall()
            }
            for e in events:
                e["liked"] = e["id"] in liked_ids

        return events


# ─── Venues ───────────────────────────────────────────────────────────────────

@router.get("/venues")
def list_venues(q: Optional[str] = None, limit: int = 10):
    with get_db() as conn:
        if q:
            rows = conn.execute(
                "SELECT DISTINCT venue FROM events WHERE venue LIKE ? AND venue IS NOT NULL AND venue != '' ORDER BY venue LIMIT ?",
                (f"%{q}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT venue FROM events WHERE venue IS NOT NULL AND venue != '' ORDER BY venue LIMIT ?",
                (limit,),
            ).fetchall()
        return [r[0] for r in rows]


# ─── Likes ────────────────────────────────────────────────────────────────────

@router.post("/events/{event_id}/like")
def like_event(event_id: int, user_id: int):
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone():
            raise HTTPException(404, "Event not found")
        if not conn.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
            raise HTTPException(404, "User not found")
        try:
            conn.execute(
                "INSERT INTO likes (user_id, event_id) VALUES (?, ?)", (user_id, event_id)
            )
        except Exception:
            raise HTTPException(400, "Already liked")
        return {"user_id": user_id, "event_id": event_id, "liked": True}


@router.delete("/events/{event_id}/like")
def unlike_event(event_id: int, user_id: int):
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM likes WHERE user_id=? AND event_id=?", (user_id, event_id)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Like not found")
        return {"user_id": user_id, "event_id": event_id, "liked": False}


# ─── Recommendations ──────────────────────────────────────────────────────────

@router.get("/recommendations/{user_id}")
def recommendations(user_id: int, limit: int = 20):
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
            raise HTTPException(404, "User not found")
    return get_recommendations(user_id, limit)


# ─── Users ────────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()
        return [row_to_dict(r) for r in rows]


@router.post("/users", status_code=201)
def create_user(body: UserCreate):
    username = body.username.strip()
    if not username:
        raise HTTPException(400, "Username cannot be empty")
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count >= 10:
            raise HTTPException(400, "Maximum 10 users allowed")
        if conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            raise HTTPException(400, "Username already taken")
        conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return row_to_dict(row)


# ─── Scraper ──────────────────────────────────────────────────────────────────

@router.get("/scraper/run")
def trigger_scrape():
    t = threading.Thread(target=run_all_scrapers, daemon=True)
    t.start()
    return {"status": "started", "message": "Scraper run started in background"}


@router.get("/scraper/logs")
def scraper_logs(limit: int = 100):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scraper_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [row_to_dict(r) for r in rows]


@router.get("/scraper/status")
def scraper_status():
    with get_db() as conn:
        last = conn.execute(
            "SELECT created_at FROM scraper_logs ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {"last_run": last[0] if last else None, "event_count": count}


# ─── Register router + serve frontend ─────────────────────────────────────────

app.include_router(router)

DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
