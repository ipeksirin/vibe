"""
Meyhane & Fasıl Mekanları — OpenStreetMap Overpass API
Rakı, meze, fasıl, türkü — İstanbul meyhane kültürü.
"""
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
from bs4 import BeautifulSoup
from scrapers.base import fetch_json

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Geniş meyhane/rakı/meze sorgusu — İstanbul bbox
OVERPASS_QUERY = """
[out:json][timeout:45];
(
  nwr["name"~"meyhane|fasıl|fasil|türkü|raki bar|rakı bar",i]
     ["amenity"~"restaurant|bar|pub|cafe"]
     (40.85,28.60,41.20,29.40);
  nwr["amenity"~"restaurant|bar"]
     ["cuisine"~"turkish|meze|raki",i]
     (40.85,28.60,41.20,29.40);
  nwr["amenity"~"restaurant|bar"]
     ["drink:raki"="yes"]
     (40.85,28.60,41.20,29.40);
  nwr["amenity"~"restaurant|bar"]
     ["name"~"balık|balik|taverna|taverma|ocakbaşı|ocakbasi",i]
     ["cuisine"~"turkish|seafood",i]
     (40.85,28.60,41.20,29.40);
  nwr["amenity"~"restaurant|bar"]
     ["name"~"lokanta|meyhane|meze|rakı|raki",i]
     (40.85,28.60,41.20,29.40);
);
out center tags;
"""

DISTRICTS = [
    ("Kadıköy",  40.960, 29.010, 40.995, 29.090),
    ("Beyoğlu",  41.010, 28.955, 41.050, 29.005),
    ("Beşiktaş", 41.030, 29.000, 41.075, 29.045),
    ("Üsküdar",  41.010, 29.010, 41.065, 29.080),
    ("Şişli",    41.045, 28.965, 41.085, 29.015),
    ("Fatih",    40.990, 28.890, 41.030, 28.980),
    ("Sarıyer",  41.080, 29.010, 41.160, 29.080),
    ("Karaköy",  41.018, 28.970, 41.032, 28.990),
    ("Moda",     40.974, 29.023, 40.984, 29.040),
    ("Bağcılar", 41.030, 28.840, 41.060, 28.880),
]

# Yer adında olması gereken — gürültülü sonuçları filtrele
MEYHANE_SIGNALS = {
    "meyhane", "fasıl", "fasil", "türkü", "raki", "rakı",
    "meze", "balık", "balik", "taverna", "ocakbaşı", "ocakbasi",
}


def _get_district(lat: float, lon: float, tags: dict) -> str:
    for tag in ("addr:district", "addr:suburb", "addr:quarter", "addr:neighbourhood"):
        val = tags.get(tag, "").strip()
        if val:
            return val
    for name, min_lat, min_lon, max_lat, max_lon in DISTRICTS:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return name
    return "Istanbul"


def _fetch_og_image(url: str) -> str:
    try:
        with httpx.Client(timeout=8, follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = client.get(url)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for prop in ("og:image", "twitter:image"):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag:
                content = tag.get("content", "").strip()
                if content and content.startswith("http"):
                    return content
    except Exception:
        pass
    return ""


def _get_image(tags: dict) -> str:
    # 1. Doğrudan image tag'i
    img = tags.get("image", "").strip()
    if img and img.startswith("http"):
        return img

    # 2. Wikimedia Commons
    wmc = tags.get("wikimedia_commons", "").strip()
    if wmc:
        # "File:Foo.jpg" → URL
        filename = wmc.replace("File:", "").replace("Category:", "")
        if filename:
            encoded = urllib.parse.quote(filename.replace(" ", "_"))
            return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=400"

    # 3. Mapillary (sadece varsa)
    mapillary = tags.get("mapillary", "").strip()
    if mapillary:
        return f"https://images.mapillary.com/{mapillary}/thumb-320.jpg"

    return ""


def scrape() -> list[dict]:
    data = fetch_json(OVERPASS_URL, params={"data": OVERPASS_QUERY})
    if not data:
        logger.warning("Meyhane/Overpass: veri gelmedi")
        return []

    events = []
    seen = set()

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue

        # Sadece gerçek meyhane sinyali taşıyanları al
        name_lower = name.lower()
        has_signal = any(s in name_lower for s in MEYHANE_SIGNALS)
        has_cuisine = any(s in tags.get("cuisine", "").lower() for s in ("turkish", "meze", "raki"))
        has_raki_tag = tags.get("drink:raki") == "yes"
        if not (has_signal or has_cuisine or has_raki_tag):
            continue

        if name in seen:
            continue
        seen.add(name)

        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if not lat or not lon:
            continue

        district = _get_district(float(lat), float(lon), tags)

        osm_type = element.get("type", "node")
        osm_id = element.get("id", "")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

        website = tags.get("website", "") or tags.get("contact:website", "") or tags.get("url", "")
        image_url = _get_image(tags)

        address = tags.get("addr:street", "")
        if tags.get("addr:housenumber"):
            address = f"{address} {tags['addr:housenumber']}".strip()

        events.append({
            "title": name,
            "venue": name,
            "date": "",
            "genres": ["meyhane"],
            "city": district,
            "ticket_url": website or source_url,
            "image_url": image_url,
            "_website": website,   # geçici, og:image için
            "source_url": source_url,
        })

    # Website olan mekânlar için paralel og:image çek
    needs_image = [(i, e["_website"]) for i, e in enumerate(events)
                   if not e["image_url"] and e["_website"]]
    if needs_image:
        logger.info(f"Meyhane: {len(needs_image)} mekan için og:image çekiliyor...")
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(_fetch_og_image, url): i for i, url in needs_image}
            for future in as_completed(futures):
                idx = futures[future]
                img = future.result()
                if img:
                    events[idx]["image_url"] = img

    # Geçici _website alanını temizle
    for e in events:
        e.pop("_website", None)

    logger.info(f"Meyhane/Overpass: {len(events)} mekan bulundu")
    return events
