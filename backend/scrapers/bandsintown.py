"""
Bandsintown — Istanbul events via their public API
https://www.bandsintown.com
Note: Uses the public /artists endpoint. No key needed for basic usage.
"""
import logging
from datetime import datetime, timedelta
from scrapers.base import fetch_json, infer_genres

logger = logging.getLogger(__name__)

# Popular artists known to play Istanbul — we fetch their events and filter by city
# A broader approach: use the city events search
SEARCH_URL = "https://rest.bandsintown.com/v1.0/venues/search"
CITY_URL = "https://rest.bandsintown.com/v1.0/events"


def scrape() -> list[dict]:
    today = datetime.utcnow().date()
    end = today + timedelta(days=90)

    params = {
        "city": "Istanbul",
        "country": "Turkey",
        "date": f"{today},{end}",
        "per_page": 50,
        "app_id": "vibe_app",
    }

    data = fetch_json(CITY_URL, params=params)
    if not data or isinstance(data, dict) and data.get("error"):
        logger.warning("Bandsintown city API unavailable, trying fallback")
        return []

    items = data if isinstance(data, list) else data.get("data", [])
    events = []

    for item in items:
        title = ""
        lineup = item.get("lineup") or []
        if lineup:
            title = ", ".join(lineup)
        if not title:
            title = item.get("title", "")
        if not title:
            continue

        venue_obj = item.get("venue") or {}
        venue = venue_obj.get("name", "")
        city = venue_obj.get("city", "")
        if city.lower() not in ("istanbul", "i̇stanbul"):
            continue  # filter to Istanbul only

        date_str = (item.get("datetime") or item.get("starts_at", ""))[:16]
        image_url = item.get("artist_image_url", "") or item.get("image_url", "")
        source_url = item.get("url", "")

        events.append({
            "title": title, "venue": venue, "date": date_str,
            "genres": infer_genres(title, venue), "city": "Istanbul",
            "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
        })

    logger.info(f"Bandsintown: found {len(events)} events")
    return events
