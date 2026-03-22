"""
Passo — https://www.passo.com.tr
"""
import logging
from scrapers.base import fetch, fetch_json, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.passo.com.tr"
API = f"{BASE}/api/search?category=&city=istanbul&q=&page=1&pageSize=50"


def scrape() -> list[dict]:
    # Try JSON API first
    data = fetch_json(API)
    if data:
        items = data if isinstance(data, list) else data.get("data", data.get("items", data.get("result", [])))
        if items and isinstance(items, list):
            return _parse_api(items)

    # Fallback to HTML
    soup = fetch(f"{BASE}/istanbul")
    if not soup:
        return []

    events = []
    for card in soup.select(".event-item, .event-card, article"):
        try:
            title_el = card.select_one("h2, h3, .title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href
            venue_el = card.select_one(".venue, .location, .place")
            venue = venue_el.get_text(strip=True) if venue_el else ""
            date_el = card.select_one(".date, time")
            date_str = date_el.get_text(strip=True) if date_el else ""
            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""
            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": infer_genres(title, venue), "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception:
            continue

    logger.info(f"Passo: found {len(events)} events")
    return events


def _parse_api(items: list) -> list[dict]:
    events = []
    for item in items:
        title = item.get("name", "") or item.get("title", "")
        if not title:
            continue
        venue = item.get("venueName", "") or item.get("venue", "")
        date_str = (item.get("startDate", "") or item.get("date", ""))[:16]
        image_url = item.get("imageUrl", "") or item.get("image", "")
        slug = item.get("slug", "") or item.get("id", "")
        source_url = f"{BASE}/etkinlik/{slug}" if slug else ""
        events.append({
            "title": title, "venue": venue, "date": date_str,
            "genres": infer_genres(title, venue), "city": "Istanbul",
            "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
        })
    logger.info(f"Passo API: found {len(events)} events")
    return events
