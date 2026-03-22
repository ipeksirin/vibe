"""
Biletix — Turkish ticketing platform
https://www.biletix.com/anasayfa/TURKIYE/tr
Note: Site uses heavy JS rendering; this attempts the JSON API endpoint.
"""
import logging
from datetime import datetime, timedelta
from scrapers.base import fetch_json, fetch, infer_genres

logger = logging.getLogger(__name__)

LISTING_URL = "https://www.biletix.com/search/TURKIYE/tr#0"
API_URL = "https://www.biletix.com/solr/query?q=sehir:ISTANBUL&rows=60&sort=tarih+asc&wt=json"


def scrape() -> list[dict]:
    data = fetch_json(API_URL)
    if not data:
        return _scrape_html()

    events = []
    docs = data.get("response", {}).get("docs", [])
    for doc in docs:
        title = doc.get("baslik_tr", "") or doc.get("baslik", "")
        if not title:
            continue
        venue = doc.get("mekan", "") or doc.get("mekan_tr", "")
        date_str = (doc.get("tarih") or "")[:16]
        image_url = doc.get("kapak_resim", "")
        event_id = doc.get("id", "")
        source_url = f"https://www.biletix.com/etkinlik/{event_id}/TURKIYE/tr" if event_id else ""
        genres = infer_genres(title, venue)

        events.append({
            "title": title,
            "venue": venue,
            "date": date_str,
            "genres": genres,
            "city": "Istanbul",
            "ticket_url": source_url,
            "image_url": image_url,
            "source_url": source_url,
        })

    logger.info(f"Biletix: found {len(events)} events")
    return events


def _scrape_html() -> list[dict]:
    soup = fetch("https://www.biletix.com/anasayfa/TURKIYE/tr")
    if not soup:
        return []
    events = []
    for card in soup.select(".event-item, .etkinlik-kart, article"):
        try:
            title_el = card.select_one("h2, h3, .title, .event-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            link = card.select_one("a")
            source_url = link["href"] if link and link.get("href") else ""
            if source_url and not source_url.startswith("http"):
                source_url = "https://www.biletix.com" + source_url
            venue_el = card.select_one(".venue, .mekan")
            venue = venue_el.get_text(strip=True) if venue_el else ""
            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""
            events.append({
                "title": title, "venue": venue, "date": "",
                "genres": infer_genres(title, venue),
                "city": "Istanbul", "ticket_url": source_url,
                "image_url": image_url, "source_url": source_url,
            })
        except Exception:
            continue
    return events
