"""
Zorlu PSM — https://www.zorlu.com.tr/etkinlikler
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.zorlu.com.tr"
URL = f"{BASE}/etkinlikler"


def scrape() -> list[dict]:
    soup = fetch(URL)
    if not soup:
        return []

    events = []
    cards = soup.select(".event-card, .etkinlik-card, article, .event-item, .col-event")

    for card in cards:
        try:
            title_el = card.select_one("h2, h3, h4, .event-title, .title, [class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, .date, [class*='date'], [class*='tarih']")
            date_str = ""
            if date_el:
                date_str = date_el.get("datetime", "") or date_el.get_text(strip=True)

            img_el = card.select_one("img")
            image_url = ""
            if img_el:
                image_url = img_el.get("src", "") or img_el.get("data-src", "") or img_el.get("data-lazy-src", "")
                if image_url and not image_url.startswith("http"):
                    image_url = BASE + image_url

            venue = "Zorlu PSM"
            genres = infer_genres(title, venue)

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": genres, "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Zorlu parse error: {e}")

    logger.info(f"Zorlu PSM: found {len(events)} events")
    return events
