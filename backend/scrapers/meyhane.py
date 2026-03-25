"""
Meyhane & Fasıl Mekanları — Foursquare Places API
Rakı, meze, fasıl — İstanbul meyhane kültürü.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import httpx

# .env dosyasından yükle
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            if "=" in _line and not _line.startswith("#"):
                _k, _v = _line.strip().split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

FSQ_KEY = os.environ.get("FOURSQUARE_API_KEY", "")

logger = logging.getLogger(__name__)

FSQ_BASE = "https://api.foursquare.com/v3"

# İstanbul ilçeleri — merkez koordinatları
DISTRICTS = [
    ("Kadıköy",  40.9833, 29.0299),
    ("Beyoğlu",  41.0338, 28.9743),
    ("Beşiktaş", 41.0430, 29.0057),
    ("Üsküdar",  41.0230, 29.0152),
    ("Şişli",    41.0602, 28.9877),
    ("Fatih",    41.0166, 28.9397),
    ("Sarıyer",  41.1651, 29.0576),
    ("Karaköy",  41.0228, 28.9742),
    ("Moda",     40.9796, 29.0304),
    ("Balat",    41.0297, 28.9494),
    ("Asmalımescit", 41.0303, 28.9753),
    ("Çengelköy", 41.0573, 29.0699),
]

# Foursquare kategori ID — Bar & Nightlife > Bar
# 13003 = Bar, 13065 = Raki Bar, 13032 = Lounge
FSQ_CATEGORIES = "13003,13065,13032"

# Arama terimleri
SEARCH_QUERIES = ["meyhane", "fasıl", "rakı bar", "meze restaurant"]

# Adında bu kelimelerden biri olmayan yerleri çıkar
MEYHANE_SIGNALS = {
    "meyhane", "fasıl", "fasil", "rakı", "raki", "meze",
    "balık evi", "balik evi", "taverna", "ocakbaşı", "ocakbasi",
}

# Kesinlikle meyhane olmayan yer türleri — çıkar
EXCLUDE_SIGNALS = {
    "mantı", "manti", "döner", "doner", "cafe", "kahve",
    "türkü evi", "turku evi", "pastane", "fırın", "firin",
    "pizza", "burger", "sushi", "noodle",
}


def _fetch_places(query: str, lat: float, lon: float) -> list[dict]:
    if not FSQ_KEY:
        return []
    headers = {"Authorization": FSQ_KEY, "Accept": "application/json"}
    params = {
        "query": query,
        "ll": f"{lat},{lon}",
        "radius": 1500,
        "limit": 50,
        "categories": FSQ_CATEGORIES,
        "fields": "fsq_id,name,location,photos,website,categories",
    }
    try:
        with httpx.Client(timeout=10, headers=headers) as client:
            r = client.get(f"{FSQ_BASE}/places/search", params=params)
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"FSQ search error ({query} @ {lat},{lon}): {e}")
        return []


def _get_photo(fsq_id: str) -> str:
    if not FSQ_KEY:
        return ""
    headers = {"Authorization": FSQ_KEY, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=8, headers=headers) as client:
            r = client.get(f"{FSQ_BASE}/places/{fsq_id}/photos", params={"limit": 1})
            r.raise_for_status()
            photos = r.json()
            if photos:
                p = photos[0]
                return f"{p['prefix']}400x300{p['suffix']}"
    except Exception as e:
        logger.debug(f"FSQ photo error {fsq_id}: {e}")
    return ""


def _is_meyhane(name: str, categories: list) -> bool:
    name_lower = name.lower()

    # Kesinlikle meyhane değilse çıkar
    if any(ex in name_lower for ex in EXCLUDE_SIGNALS):
        return False

    # Adında meyhane sinyali varsa kabul et
    if any(s in name_lower for s in MEYHANE_SIGNALS):
        return True

    # Foursquare kategorisi "Bar" veya "Raki Bar" ise kabul et
    cat_names = [c.get("name", "").lower() for c in categories]
    if any("raki" in c or "meyhane" in c or "fasil" in c or "fasıl" in c for c in cat_names):
        return True

    return False


def scrape() -> list[dict]:
    if not FSQ_KEY:
        logger.warning("Meyhane: FOURSQUARE_API_KEY eksik, scrape atlandı")
        return []

    raw: list[dict] = []

    # Her ilçe × her sorgu için paralel arama
    tasks = [(q, lat, lon, district) for district, lat, lon in DISTRICTS for q in SEARCH_QUERIES]

    def _search(task):
        query, lat, lon, district = task
        results = _fetch_places(query, lat, lon)
        return district, results

    with ThreadPoolExecutor(max_workers=8) as pool:
        for district, results in pool.map(_search, tasks):
            for place in results:
                place["_district"] = district
                raw.append(place)

    # Tekrar edenleri ve alakasızları çıkar
    seen: set[str] = set()
    events: list[dict] = []

    for place in raw:
        fsq_id = place.get("fsq_id", "")
        if fsq_id in seen:
            continue

        name = place.get("name", "").strip()
        if not name:
            continue

        categories = place.get("categories", [])
        if not _is_meyhane(name, categories):
            continue

        seen.add(fsq_id)

        loc = place.get("location", {})
        district = place.get("_district") or loc.get("locality", "Istanbul")

        # Fotoğraf — önce inline, yoksa ayrı istek
        photo_url = ""
        photos = place.get("photos", [])
        if photos:
            p = photos[0]
            photo_url = f"{p['prefix']}400x300{p['suffix']}"

        website = place.get("website", "") or ""
        source_url = f"https://foursquare.com/v/{fsq_id}"

        events.append({
            "title": name,
            "venue": name,
            "date": "",
            "genres": ["meyhane"],
            "city": district,
            "ticket_url": website or source_url,
            "image_url": photo_url,
            "source_url": source_url,
            "_fsq_id": fsq_id,
        })

    # Fotoğrafı olmayanlar için ayrı istek at
    needs_photo = [(i, e) for i, e in enumerate(events) if not e["image_url"]]
    if needs_photo:
        logger.info(f"Meyhane: {len(needs_photo)} mekan için fotoğraf çekiliyor...")
        def _fetch(item):
            i, e = item
            return i, _get_photo(e["_fsq_id"])
        with ThreadPoolExecutor(max_workers=8) as pool:
            for i, img in pool.map(_fetch, needs_photo):
                if img:
                    events[i]["image_url"] = img

    # Geçici alanları temizle
    for e in events:
        e.pop("_fsq_id", None)

    logger.info(f"Meyhane/Foursquare: {len(events)} mekan bulundu")
    return events
