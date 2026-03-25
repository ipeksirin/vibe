"""
Meyhane Mekanları — OpenStreetMap Overpass API
Sadece adında 'meyhane' geçen gerçek İstanbul meyhaneleri.
"""
import logging
import urllib.parse
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Sadece adında "meyhane" geçen yerler — hiçbir gürültü girmez
OVERPASS_QUERY = """
[out:json][timeout:45];
(
  nwr["name"~"meyhane",i]
     ["amenity"~"restaurant|bar|pub"]
     (40.85,28.60,41.20,29.40);
);
out center tags;
"""

DISTRICTS = [
    ("Kadıköy",      40.960, 29.010, 40.995, 29.090),
    ("Beyoğlu",      41.010, 28.955, 41.050, 29.005),
    ("Beşiktaş",     41.030, 29.000, 41.075, 29.045),
    ("Üsküdar",      41.010, 29.010, 41.065, 29.080),
    ("Şişli",        41.045, 28.965, 41.085, 29.015),
    ("Fatih",        40.990, 28.890, 41.030, 28.980),
    ("Sarıyer",      41.080, 29.010, 41.160, 29.080),
    ("Karaköy",      41.018, 28.970, 41.032, 28.990),
    ("Moda",         40.974, 29.023, 40.984, 29.040),
    ("Asmalımescit", 41.028, 28.971, 41.035, 28.980),
]


def _get_district(lat: float, lon: float) -> str:
    for name, min_lat, min_lon, max_lat, max_lon in DISTRICTS:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return name
    return "Istanbul"


def _get_image(tags: dict) -> str:
    img = tags.get("image", "").strip()
    if img and img.startswith("http"):
        return img
    wmc = tags.get("wikimedia_commons", "").strip()
    if wmc:
        filename = wmc.replace("File:", "").replace("Category:", "")
        if filename:
            encoded = urllib.parse.quote(filename.replace(" ", "_"))
            return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=400"
    return ""


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


def scrape() -> list[dict]:
    try:
        with httpx.Client(timeout=50) as client:
            r = client.post(OVERPASS_URL, data={"data": OVERPASS_QUERY})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"Meyhane/Overpass hata: {e}")
        return []

    events = []
    seen = set()

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue

        # Sadece adında "meyhane" geçenler
        if "meyhane" not in name.lower():
            continue

        if name in seen:
            continue
        seen.add(name)

        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if not lat or not lon:
            continue

        district = _get_district(float(lat), float(lon))

        osm_type = element.get("type", "node")
        osm_id = element.get("id", "")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
        website = tags.get("website", "") or tags.get("contact:website", "") or tags.get("url", "")
        image_url = _get_image(tags)

        events.append({
            "title": name,
            "venue": name,
            "date": "",
            "genres": ["meyhane"],
            "city": district,
            "ticket_url": website or source_url,
            "image_url": image_url,
            "_website": website,
            "source_url": source_url,
        })

    # Fotoğrafı olmayanlar için website'den og:image çek
    for e in events:
        if not e["image_url"] and e.get("_website"):
            e["image_url"] = _fetch_og_image(e["_website"])
        e.pop("_website", None)

    logger.info(f"Meyhane/Overpass: {len(events)} mekan bulundu")
    return events
