"""
Harbiye Açıkhava — Istanbul Metropolitan Municipality
https://www.ibb.istanbul
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.ibb.istanbul"
URLS = [
    f"{BASE}/etkinlikler",
    "https://www.ibb.istanbul/Haberler/Etkinlikler",
]


def scrape() -> list[dict]:
    soup = None
    for url in URLS:
        soup = fetch(url)
        if soup:
            break
    if not soup:
        return []

    events = []
    for card in soup.select(".event-card, article, .event-item, .etkinlik-kart, .news-item, .card"):
        try:
            title_el = card.select_one("h2, h3, h4, .title, .event-title, .card-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one("time, .date, [class*='date'], .tarih")
            date_str = date_el.get("datetime", "") or (date_el.get_text(strip=True) if date_el else "")

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
            if image_url and not image_url.startswith("http"):
                image_url = BASE + image_url

            venue = "Harbiye Açıkhava"
            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": infer_genres(title, venue), "city": "Istanbul",
                "ticket_url": source_url, "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Harbiye parse error: {e}")

    logger.info(f"Harbiye (IBB): found {len(events)} events")
    return events
