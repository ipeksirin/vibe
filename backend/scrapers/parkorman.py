"""
Bonus Parkorman — https://www.parkorman.com
Outdoor electronic / festival events.
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.parkorman.com"


def scrape() -> list[dict]:
    for url in [f"{BASE}/events", f"{BASE}/etkinlikler", BASE]:
        soup = fetch(url)
        if soup:
            break
    else:
        return []

    events = []
    for card in soup.select(".event-card, article, .event-item, .event, .show"):
        try:
            title_el = card.select_one("h2, h3, h4, .title, .event-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, .date, [class*='date']")
            date_str = date_el.get("datetime", "") or (date_el.get_text(strip=True) if date_el else "")

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""

            venue = "Bonus Parkorman"
            genres = infer_genres(title, venue)
            for g in ["electronic", "festival"]:
                if g not in genres:
                    genres.append(g)

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": genres, "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Parkorman parse error: {e}")

    logger.info(f"Bonus Parkorman: found {len(events)} events")
    return events
