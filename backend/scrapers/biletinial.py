"""
Biletinial — https://biletinial.com/tr-tr/muzik?sehir=istanbul
Parses .kategori__etkinlikler > ul > li cards directly from the HTML listing.
"""
import re
import logging
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://biletinial.com"

PAGES = [
    f"{BASE}/tr-tr/muzik?sehir=istanbul",
    f"{BASE}/tr-tr/tiyatro?sehir=istanbul",
    f"{BASE}/tr-tr/festival?sehir=istanbul",
]

MONTH_MAP = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
}


def _parse_date(text: str) -> str:
    """Convert 'Ağustos - 01' or '01 Ağustos' → '2026-08-01'."""
    text = text.strip().lower()
    for month_tr, month_num in MONTH_MAP.items():
        if month_tr in text:
            day_match = re.search(r"\d{1,2}", text)
            if day_match:
                day = day_match.group(0).zfill(2)
                return f"2026-{month_num}-{day}"
    return ""


def _parse_items(soup) -> list[dict]:
    container = soup.select_one(".kategori__etkinlikler")
    if not container:
        return []

    events = []
    for li in container.select("li"):
        try:
            # Title
            h3 = li.select_one("h3")
            title = h3.get_text(strip=True) if h3 else ""
            if not title:
                continue

            # Link
            a = li.select_one("figure a, h3 a")
            href = a.get("href", "") if a else ""
            source_url = BASE + href if href and not href.startswith("http") else href

            # Image
            img = li.select_one("img")
            image_url = img.get("src", "") if img else ""

            # Venue — <address><b>İstanbul Avrupa</b><small>Life Park</small></address>
            addr = li.select_one("address")
            venue = ""
            if addr:
                small = addr.select_one("small")
                venue = small.get_text(strip=True) if small else addr.get_text(strip=True)
            if not venue:
                venue = "Istanbul"
            # Normalize venue name variants
            venue = venue.replace("Life Park", "Lifepark")

            # Date — <span>Ağustos - 01</span> (last span in li)
            spans = li.select("span")
            date_str = ""
            for span in reversed(spans):
                txt = span.get_text(strip=True)
                if any(m in txt.lower() for m in MONTH_MAP):
                    date_str = _parse_date(txt)
                    break

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
        except Exception as e:
            logger.error(f"Biletinial li parse error: {e}")

    return events


def scrape() -> list[dict]:
    all_events = []
    seen_urls = set()

    for url in PAGES:
        soup = fetch(url)
        if not soup:
            continue
        items = _parse_items(soup)
        for ev in items:
            if ev["source_url"] not in seen_urls:
                seen_urls.add(ev["source_url"])
                all_events.append(ev)

    logger.info(f"Biletinial: found {len(all_events)} events")
    return all_events
