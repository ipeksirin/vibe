"""
Lifepark — https://www.lifepark.com.tr
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.lifepark.com.tr"


def scrape() -> list[dict]:
    soup = fetch(BASE)
    if not soup:
        return []

    events = []
    for card in soup.select(".event-card, article, .event-item, .etkinlik, .show"):
        try:
            title_el = card.select_one("h2, h3, h4, .title, .event-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, .date, .tarih")
            date_str = date_el.get("datetime", "") or (date_el.get_text(strip=True) if date_el else "")

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""

            venue = "Lifepark"
            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": infer_genres(title, venue), "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception:
            continue

    logger.info(f"Lifepark: found {len(events)} events")
    return events
