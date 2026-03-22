"""
Eventbrite Turkey — Istanbul events (HTML scrape)
"""
import logging
import re
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE_URL = "https://www.eventbrite.com/d/turkey--istanbul/music/"


def scrape() -> list[dict]:
    soup = fetch(BASE_URL)
    if not soup:
        return []

    events = []
    cards = soup.select("[data-testid='search-event-card-wrapper'], .search-event-card, article.eds-event-card")

    for card in cards:
        try:
            title_el = card.select_one("h2, .eds-event-card__formatted-name, [data-testid='event-card-title']")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href*='/e/']")
            source_url = link_el["href"] if link_el and link_el.get("href") else ""
            if source_url and not source_url.startswith("http"):
                source_url = "https://www.eventbrite.com" + source_url

            date_el = card.select_one("time, [data-testid='event-card-date'], p.eds-text-bm")
            date_str = date_el.get_text(strip=True) if date_el else ""

            venue_el = card.select_one("[data-testid='event-card-venue'], .card-text--truncated__two, .eds-text-bs--fixed")
            venue = venue_el.get_text(strip=True) if venue_el else "Istanbul"

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""

            genres = infer_genres(title, venue)

            events.append(
                {
                    "title": title,
                    "venue": venue,
                    "date": date_str,
                    "genres": genres,
                    "city": "Istanbul",
                    "ticket_url": source_url,
                    "image_url": image_url,
                    "source_url": source_url,
                }
            )
        except Exception as e:
            logger.error(f"Eventbrite card parse error: {e}")
            continue

    logger.info(f"Eventbrite: found {len(events)} events")
    return events
