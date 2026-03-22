"""
Salon IKSV — https://www.iksv.org/salonIKSV
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.iksv.org"
URL = f"{BASE}/salonIKSV"


def scrape() -> list[dict]:
    soup = fetch(URL)
    if not soup:
        return []

    events = []
    for card in soup.select(".event-card, article, .event-item, .program-item, .etkinlik, li.event"):
        try:
            title_el = card.select_one("h2, h3, h4, .title, .event-title, .program-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, .date, [class*='date'], [class*='tarih']")
            date_str = date_el.get("datetime", "") or (date_el.get_text(strip=True) if date_el else "")

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
            if image_url and not image_url.startswith("http"):
                image_url = BASE + image_url

            venue = "Salon IKSV"
            genres = infer_genres(title, venue)
            if "classical" not in genres and "jazz" not in genres:
                genres = ["classical", "live"] + genres

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": genres, "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Salon IKSV parse error: {e}")

    logger.info(f"Salon IKSV: found {len(events)} events")
    return events
