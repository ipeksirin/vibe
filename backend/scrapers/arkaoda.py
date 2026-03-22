"""
Arkaoda — https://arkaoda.com
Independent music venue, indie/alternative/underground.
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://arkaoda.com"
URL = f"{BASE}/etkinlikler"


def scrape() -> list[dict]:
    soup = fetch(URL)
    if not soup:
        soup = fetch(BASE)
    if not soup:
        return []

    events = []
    # Arkaoda uses WordPress, try common WP patterns
    for card in soup.select(".event-card, .tribe-event, .tribe-events-calendar-list__event, article, .event-item, .wp-block-post"):
        try:
            title_el = card.select_one("h2, h3, h4, .tribe-event-url, .entry-title, .title, .event-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, abbr.tribe-events-abbr, .tribe-event-date-start, .date, [class*='date']")
            date_str = ""
            if date_el:
                date_str = date_el.get("datetime", "") or date_el.get("title", "") or date_el.get_text(strip=True)

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""

            venue = "Arkaoda"
            genres = infer_genres(title, venue)
            for g in ["indie", "live"]:
                if g not in genres:
                    genres.append(g)

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": genres, "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Arkaoda parse error: {e}")

    logger.info(f"Arkaoda: found {len(events)} events")
    return events
