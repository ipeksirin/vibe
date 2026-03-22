"""
Biletinial — https://www.biletinial.com
"""
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.biletinial.com"
URL = f"{BASE}/etkinlikler?sehir=istanbul"


def scrape() -> list[dict]:
    soup = fetch(URL)
    if not soup:
        return []

    events = []
    cards = soup.select(".event-card, .etkinlik-kart, article, .col-event")

    for card in cards:
        try:
            title_el = card.select_one("h2, h3, .event-name, .title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            source_url = href if href.startswith("http") else BASE + href

            date_el = card.select_one(".date, .tarih, time")
            date_str = date_el.get_text(strip=True) if date_el else ""

            venue_el = card.select_one(".venue, .mekan, .location")
            venue = venue_el.get_text(strip=True) if venue_el else ""

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
            if image_url and not image_url.startswith("http"):
                image_url = BASE + image_url

            events.append({
                "title": title, "venue": venue, "date": date_str,
                "genres": infer_genres(title, venue),
                "city": "Istanbul", "ticket_url": source_url,
                "image_url": image_url, "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Biletinial parse error: {e}")

    logger.info(f"Biletinial: found {len(events)} events")
    return events
