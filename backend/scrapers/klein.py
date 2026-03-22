"""
Klein Istanbul — https://www.kleinistanbul.com
Underground electronic / techno club.
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.kleinistanbul.com"


def scrape() -> list[dict]:
    for url in [f"{BASE}/events", f"{BASE}/etkinlikler", BASE]:
        soup = fetch(url)
        if soup:
            break
    else:
        return []

    events = []
    for card in soup.select(".event-card, article, .event, .show, li.event, .event-item"):
        try:
            title_el = card.select_one("h2, h3, h4, .title, .event-title, .name")
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

            venue = "Klein"
            genres = infer_genres(title, venue)
            # Klein is primarily electronic/techno
            for g in ["electronic", "dj-set"]:
                if g not in genres:
                    genres.insert(0, g)

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": genres, "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Klein parse error: {e}")

    logger.info(f"Klein: found {len(events)} events")
    return events
