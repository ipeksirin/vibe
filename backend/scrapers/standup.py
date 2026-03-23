"""
Stand-up & Komedi — Biletix API (tüm İstanbul etkinlikleri, komedi filtreli)
+ Biletinial tiyatro sayfasından komedi/stand-up filtrelemesi
"""
import re
import logging
from scrapers.base import fetch_json, fetch

logger = logging.getLogger(__name__)

# Çalışan Biletix API — tüm İstanbul, daha fazla satır
BILETIX_API = (
    "https://www.biletix.com/solr/query"
    "?q=sehir:ISTANBUL&rows=200&sort=tarih+asc&wt=json"
)

# Biletinial sayfaları — tiyatro + eğlence, stand-up genellikle burada
BILETINIAL_PAGES = [
    "https://biletinial.com/tr-tr/tiyatro?sehir=istanbul",
    "https://biletinial.com/tr-tr/eglence?sehir=istanbul",
]

STANDUP_KEYWORDS = {"stand up", "standup", "stand-up", "komedi", "comedy", "güldürü", "tek kişilik"}

MONTH_MAP = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
}


def _is_standup(title: str, venue: str = "") -> bool:
    text = (title + " " + venue).lower()
    return any(kw in text for kw in STANDUP_KEYWORDS)


def _parse_date(text: str) -> str:
    text = text.strip().lower()
    for month_tr, month_num in MONTH_MAP.items():
        if month_tr in text:
            day_match = re.search(r"\d{1,2}", text)
            if day_match:
                return f"2026-{month_num}-{day_match.group(0).zfill(2)}"
    return ""


def _from_biletix() -> list[dict]:
    data = fetch_json(BILETIX_API)
    if not data:
        return []
    events = []
    for doc in data.get("response", {}).get("docs", []):
        title = doc.get("baslik_tr", "") or doc.get("baslik", "")
        if not title:
            continue
        venue = doc.get("mekan", "") or doc.get("mekan_tr", "")
        if not _is_standup(title, venue):
            continue
        date_str = (doc.get("tarih") or "")[:16]
        image_url = doc.get("kapak_resim", "")
        event_id = doc.get("id", "")
        source_url = f"https://www.biletix.com/etkinlik/{event_id}/TURKIYE/tr" if event_id else ""
        events.append({
            "title": title,
            "venue": venue,
            "date": date_str,
            "genres": ["stand-up"],
            "city": "Istanbul",
            "ticket_url": source_url,
            "image_url": image_url,
            "source_url": source_url,
        })
    logger.info(f"Standup/Biletix: {len(events)} events")
    return events


def _from_biletinial() -> list[dict]:
    events = []
    for url in BILETINIAL_PAGES:
        soup = fetch(url)
        if not soup:
            continue
        container = soup.select_one(".kategori__etkinlikler")
        if not container:
            continue
        for li in container.select("li"):
            try:
                h3 = li.select_one("h3")
                title = h3.get_text(strip=True) if h3 else ""
                if not title or not _is_standup(title):
                    continue
                a = li.select_one("figure a, h3 a")
                href = a.get("href", "") if a else ""
                source_url = "https://biletinial.com" + href if href and not href.startswith("http") else href
                img = li.select_one("img")
                image_url = img.get("src", "") if img else ""
                addr = li.select_one("address")
                venue = ""
                if addr:
                    small = addr.select_one("small")
                    venue = small.get_text(strip=True) if small else addr.get_text(strip=True)
                date_str = ""
                for span in reversed(li.select("span")):
                    txt = span.get_text(strip=True)
                    if any(m in txt.lower() for m in MONTH_MAP):
                        date_str = _parse_date(txt)
                        break
                events.append({
                    "title": title,
                    "venue": venue or "Istanbul",
                    "date": date_str,
                    "genres": ["stand-up"],
                    "city": "Istanbul",
                    "ticket_url": source_url,
                    "image_url": image_url,
                    "source_url": source_url,
                })
            except Exception as e:
                logger.error(f"Standup/Biletinial parse error: {e}")
    logger.info(f"Standup/Biletinial: {len(events)} events")
    return events


def scrape() -> list[dict]:
    seen = set()
    events = []
    for ev in _from_biletix() + _from_biletinial():
        key = ev.get("source_url") or f"{ev['title']}|{ev['date']}"
        if key and key not in seen:
            seen.add(key)
            events.append(ev)
    logger.info(f"Standup total: {len(events)} events")
    return events
