"""
Resident Advisor — Istanbul events
Uses RA's internal GraphQL API (undocumented but stable).
"""
import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

RA_API = "https://ra.co/graphql"

QUERY = """
query GET_EVENTS($filters: FilterInputDtoInput, $pageSize: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: 1, ordering: ASCENDING) {
    data {
      id
      listingDate
      event {
        id
        title
        date
        startTime
        venue { name }
        images { filename }
        buy { url }
        contentUrl
        genres { name }
      }
    }
  }
}
"""


def scrape() -> list[dict]:
    today = datetime.utcnow().date()
    end = today + timedelta(days=60)

    variables = {
        "filters": {
            "areas": {"eq": 31},       # Istanbul area ID on RA
            "listingDate": {
                "gte": str(today),
                "lte": str(end),
            },
        },
        "pageSize": 100,
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://ra.co/",
    }

    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(
                RA_API,
                json={"query": QUERY, "variables": variables},
                headers=headers,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"RA scraper failed: {e}")
        return []

    listings = (
        data.get("data", {})
        .get("eventListings", {})
        .get("data", [])
    )

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

        buy = ev.get("buy") or []
        ticket_url = buy[0].get("url", "") if buy else ""

        content_url = ev.get("contentUrl", "")
        source_url = f"https://ra.co{content_url}" if content_url else ""

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
