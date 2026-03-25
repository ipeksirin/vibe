"""
Zorlu PSM — https://zorlupsm.com/etkinlikler
"""
import logging
import re
from scrapers.base import fetch, infer_genres

logger = logging.getLogger(__name__)
BASE = "https://zorlupsm.com"
URL = f"{BASE}/etkinlikler"

# Promosyon/genel sayfalar — gerçek etkinlik değil
NON_EVENT_KEYWORDS = {
    "hediye kart", "hediye kartı", "gösterim", "mastercard", "visa",
    "psm genç", "uygulama fırsatları", "uygulama", "fırsatları",
    "abonelik", "sezon kartı", "kurumsal", "sponsorluk",
    "iletişim", "hakkımızda", "teknik", "salon kiralama",
    "psm loves", "indirim", "kampanya",
}

MONTH_MAP = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
}


def parse_turkish_date(text: str) -> str:
    text = text.lower().strip()
    for month_tr, month_num in MONTH_MAP.items():
        if month_tr in text:
            day_match = re.search(r"(\d{1,2})", text)
            if day_match:
                day = day_match.group(1).zfill(2)
                return f"2026-{month_num}-{day}"
    return ""


def scrape() -> list[dict]:
    soup = fetch(URL)
    if not soup:
        return []

    events = []
    seen_hrefs = set()

    for a in soup.select('a[href*="/etkinlikler/"]'):
        href = a.get("href", "")
        if not href or href == "/etkinlikler" or href.endswith("/etkinlikler"):
            continue
        # Remove query params for deduplication
        base_href = href.split("?")[0]
        if base_href in seen_hrefs:
            continue
        seen_hrefs.add(base_href)

        try:
            img = a.find("img")
            title = ""
            if img:
                title = img.get("alt", "").strip()
            if not title:
                # Fall back: first non-empty text node
                texts = [t.strip() for t in a.stripped_strings]
                title = texts[0] if texts else ""
            if not title or len(title) < 3:
                continue

            # Clean: Zorlu img alt = "TITLE" + "CATEGORY, DATE" + "TITLE" + "DETAYLI BİLGİ"
            # Split at first occurrence of category keywords (they appear right after the title)
            cat_pattern = r'(FESTİVAL|KONSER|TİYATRO|MÜZİKAL|SERGİ|DANS|OPERA|BALE|ÇOCUK|PSM ON AIR|ATÖLYE|PANEL)'
            title = re.split(cat_pattern, title, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            title = re.sub(r"\s+", " ", title).strip()
            if not title or len(title) < 3:
                continue

            # Promosyon ve genel sayfaları çıkar
            title_lower = title.lower()
            if any(kw in title_lower for kw in NON_EVENT_KEYWORDS):
                continue

            image_url = ""
            if img:
                image_url = img.get("src", "") or img.get("data-src", "") or ""
                if image_url and not image_url.startswith("http"):
                    image_url = BASE + image_url

            source_url = BASE + href if not href.startswith("http") else href

            # Extract date from text
            full_text = a.get_text(" ", strip=True)
            date_str = parse_turkish_date(full_text)

            genres = infer_genres(title, "Zorlu PSM")

            events.append({
                "title": title,
                "venue": "Zorlu PSM",
                "date": date_str,
                "genres": genres,
                "city": "Istanbul",
                "ticket_url": source_url,
                "image_url": image_url,
                "source_url": source_url,
            })
        except Exception as e:
            logger.error(f"Zorlu parse error: {e}")

    logger.info(f"Zorlu PSM: found {len(events)} events")
    return events
