"""
Lifepark — https://www.lifepark.com.tr/gelecek-etkinlikler/
Each event page has JSON-LD structured data with full date + image.
"""
import json
import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://www.lifepark.com.tr"
LIST_URL = f"{BASE}/gelecek-etkinlikler/"


def _fetch_event(url: str) -> dict | None:
    try:
        with httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, timeout=15, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if data.get("@type") == "Event":
                    return data
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Lifepark event fetch error {url}: {e}")
    return None


def scrape() -> list[dict]:
    soup = fetch(LIST_URL)
    if not soup:
        return []

    # Collect unique event URLs
    seen = set()
    event_urls = []
    for a in soup.select('a[href*="/etkinlik/"]'):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            event_urls.append(href)

    events = []
    for url in event_urls:
        try:
            ld = _fetch_event(url)
            if not ld:
                continue

            title = ld.get("name", "").strip()
            if not title:
                continue

            date_str = ld.get("startDate", "")
            # Normalize: "2026-06-06" → keep as-is; add time if available
            end_date = ld.get("endDate", "")

            location = ld.get("location") or {}
            venue = location.get("name", "Lifepark")

            # Image
            image_url = ""
            img = ld.get("image")
            if isinstance(img, list) and img:
                image_url = img[0] if isinstance(img[0], str) else ""
            elif isinstance(img, str):
                image_url = img

            # Offers / ticket URL
            offers = ld.get("offers") or {}
            ticket_url = ""
            if isinstance(offers, dict):
                ticket_url = offers.get("url", url)
            elif isinstance(offers, list) and offers:
                ticket_url = offers[0].get("url", url)
            if not ticket_url:
                ticket_url = url

            genres = infer_genres(title, venue)

            events.append({
                "title": title,
                "venue": venue,
                "date": date_str,
                "genres": genres,
                "city": "Istanbul",
                "ticket_url": ticket_url,
                "image_url": image_url,
                "source_url": url,
            })
        except Exception as e:
            logger.error(f"Lifepark parse error {url}: {e}")

    logger.info(f"Lifepark: found {len(events)} events")
    return events
