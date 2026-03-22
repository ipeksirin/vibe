"""
Dice.fm — Istanbul events
Uses Dice's internal API (undocumented).
"""
import logging
from datetime import datetime, timedelta
from scrapers.base import fetch_json, infer_genres

logger = logging.getLogger(__name__)

API = "https://api.dice.fm/api/v1/events"


def scrape() -> list[dict]:
    today = datetime.utcnow().date()
    params = {
        "types_filter": "event",
        "page[size]": 50,
        "filter[location]": "istanbul",
        "filter[from_date]": str(today),
        "filter[to_date]": str(today + timedelta(days=90)),
    }

    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "x-api-key": "",
            "Referer": "https://dice.fm/",
        }
        with httpx.Client(timeout=20) as client:
            r = client.get(API, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"Dice.fm API failed: {e}")
        return _scrape_html()

    items = data.get("data", []) or data if isinstance(data, list) else []
    events = []

    for item in items:
        title = item.get("name", "")
        if not title:
            continue
        venue_obj = item.get("venue") or {}
        venue = venue_obj.get("name", "")
        date_str = (item.get("date") or item.get("dates", {}).get("event_start_date", ""))[:16]
        image_url = (item.get("images") or [{}])[0].get("url", "") if item.get("images") else ""
        slug = item.get("url") or item.get("id", "")
        source_url = f"https://dice.fm/event/{slug}" if slug else ""
        ticket_url = source_url

        events.append({
            "title": title, "venue": venue, "date": date_str,
            "genres": infer_genres(title, venue), "city": "Istanbul",
            "ticket_url": ticket_url, "image_url": image_url, "source_url": source_url,
        })

    logger.info(f"Dice.fm: found {len(events)} events")
    return events


def _scrape_html() -> list[dict]:
    from scrapers.base import fetch
    soup = fetch("https://dice.fm/Istanbul")
    if not soup:
        return []
    events = []
    for card in soup.select("article, .event-card, [data-testid='event-card']"):
        try:
            title_el = card.select_one("h2, h3, [data-testid='event-name'], .title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else "https://dice.fm" + href
            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""
            events.append({
                "title": title, "venue": "", "date": "",
                "genres": infer_genres(title), "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception:
            continue
    return events
