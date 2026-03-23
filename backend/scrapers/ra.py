"""
Resident Advisor — Istanbul events
Uses RA's internal GraphQL API (undocumented but stable).
"""
import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

RA_API = "https://ra.co/graphql"

def scrape() -> list[dict]:
    today = datetime.utcnow().date()
    # Fetch up to end of 2027
    from datetime import date
    end = date(2027, 12, 31)
    date_gte = str(today - timedelta(days=1))
    date_lte = str(end)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://ra.co/",
    }

    listings = []
    for page in range(1, 10):  # max 10 pages × 100 = 1000 events
        query = (
            "query { eventListings("
            f'filters: {{ areas: {{ eq: 73 }}, listingDate: {{ gte: "{date_gte}", lte: "{date_lte}" }} }}, '
            f"pageSize: 100, page: {page}) {{ data {{ event {{ title startTime "
            "venue { name } images { filename } contentUrl genres { name } } } } }"
        )
        try:
            with httpx.Client(timeout=30) as client:
                r = client.post(RA_API, json={"query": query}, headers=headers)
                r.raise_for_status()
                data = r.json()
            page_listings = (
                (data.get("data") or {})
                .get("eventListings", {})
                .get("data", [])
            )
            if not page_listings:
                break
            listings.extend(page_listings)
            if len(page_listings) < 100:
                break  # last page
        except Exception as e:
            logger.error(f"RA scraper page {page} failed: {e}")
            break

    events = []
    for item in listings:
        ev = item.get("event") or {}
        if not ev:
            continue

        title = ev.get("title", "").strip()
        if not title:
            continue

        venue_obj = ev.get("venue") or {}
        venue = venue_obj.get("name", "")

        date_str = ev.get("startTime") or ev.get("date") or ""
        if date_str:
            date_str = date_str[:16]  # "YYYY-MM-DDTHH:MM"

        images = ev.get("images") or []
        image_url = ""
        if images:
            fname = images[0].get("filename", "")
            if fname:
                image_url = f"https://static.ra.co/images/{fname}"

        content_url = ev.get("contentUrl", "")
        source_url = f"https://ra.co{content_url}" if content_url else ""
        ticket_url = source_url  # RA ticket link is the event page

        ra_genres = [g.get("name", "") for g in (ev.get("genres") or [])]
        from scrapers.base import infer_genres
        genres = ra_genres if ra_genres else infer_genres(title, venue)
        genres = [g.lower().replace(" ", "-") for g in genres]

        events.append(
            {
                "title": title,
                "venue": venue,
                "date": date_str,
                "genres": genres,
                "city": "Istanbul",
                "ticket_url": ticket_url,
                "image_url": image_url,
                "source_url": source_url,
            }
        )

    logger.info(f"RA: found {len(events)} events")
    return events
