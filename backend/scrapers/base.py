import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch(url: str, timeout: int = 20, **kwargs) -> Optional[BeautifulSoup]:
    try:
        with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
            r = client.get(url, **kwargs)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error(f"fetch({url}): {e}")
        return None


def fetch_json(url: str, timeout: int = 20, **kwargs) -> Optional[dict | list]:
    try:
        with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
            r = client.get(url, **kwargs)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"fetch_json({url}): {e}")
        return None


# ── Genre inference ──────────────────────────────────────────────────────────

# Canonical genre set — must match frontend ALL_GENRES + special categories
STANDARD_GENRES = {
    "electronic", "techno", "house", "deep-house", "ambient",
    "rock", "metal", "alternative", "indie", "jazz",
    "classical", "pop", "hip-hop", "world-music",
    "festival", "dj-set", "live", "acoustic",
    "stand-up", "meyhane",
}

# Map non-standard → standard genres
GENRE_NORMALIZE: dict[str, str] = {
    # techno variants
    "minimal-techno": "techno",
    "industrial-techno": "techno",
    "hard-techno": "techno",
    # house variants
    "tech-house": "house",
    "afro-house": "house",
    "progressive-house": "house",
    "electro-house": "house",
    "organic-house": "deep-house",
    "melodic-house": "deep-house",
    "afrobeats": "house",
    # electronic variants
    "electronica": "electronic",
    "electro": "electronic",
    "club": "electronic",
    "drum-&-bass": "electronic",
    "dnb": "electronic",
    "dubstep": "electronic",
    "acid": "electronic",
    "hardcore": "electronic",
    "psytrance": "electronic",
    "trance": "electronic",
    "minimal": "electronic",
    "industrial": "electronic",
    "experimental": "electronic",
    "bass": "electronic",
    "breaks": "electronic",
    "garage": "electronic",
    "uk-garage": "electronic",
    # ambient variants
    "downtempo": "ambient",
    "chillout": "ambient",
    "drone": "ambient",
    # world music
    "afrobeat": "world-music",
    "latin": "world-music",
    "reggae": "world-music",
    "disco": "world-music",
    "funk": "world-music",
    "soul": "world-music",
    "blues": "world-music",
    "folk": "world-music",
    "türkü": "world-music",
    "fasıl": "world-music",
    # hip-hop
    "r&b": "hip-hop",
    "rnb": "hip-hop",
    "rap": "hip-hop",
    "trap": "hip-hop",
}

_GENRE_KEYWORDS: dict[str, list[str]] = {
    "electronic": ["electronic", "elektro", "edm", "electronik", "elektronik"],
    "techno": ["techno"],
    "house": ["tech house", "house music"],
    "deep-house": ["deep house", "deep-house"],
    "ambient": ["ambient", "atmosfer"],
    "rock": [" rock", "rock ", "rok"],
    "metal": ["metal", "heavy metal", "death metal", "black metal"],
    "alternative": ["alternative", "alternatif"],
    "indie": ["indie"],
    "jazz": ["jazz", "caz"],
    "classical": ["klasik", "classical", "symphony", "orkestra", "filarmoni", "oda müziği", "opera", "keman", "piyano"],
    "pop": [" pop ", "pop müzik"],
    "hip-hop": ["hip hop", "hip-hop", "rap", "r&b", "rnb"],
    "world-music": ["world music", "dünya müziği", "ethnic", "folk", "halk müziği", "türkü", "fasıl"],
    "festival": ["festival", " fest "],
    "dj-set": ["dj set", "dj-set", "b2b"],
    "acoustic": ["acoustic", "akustik", "unplugged"],
    "stand-up": ["stand up", "stand-up", "standup", "komedi", "comedy"],
    "meyhane": ["meyhane"],
}

_VENUE_GENRES: dict[str, list[str]] = {
    "nardis": ["jazz", "live"],
    "klein": ["electronic", "techno", "dj-set"],
    "arkaoda": ["indie", "alternative", "live"],
    "dorock": ["rock", "metal", "live"],
    "babylon": ["live", "indie", "alternative"],
    "salon iksv": ["classical", "jazz", "live"],
    "issanat": ["classical", "jazz", "live"],
    "parkorman": ["electronic", "festival", "dj-set"],
    "blind": ["electronic", "techno", "dj-set"],
}


def normalize_genres(genres: list[str]) -> list[str]:
    """Map any genre to the canonical standard set."""
    result = []
    seen = set()
    for g in genres:
        g = g.lower().strip()
        normalized = GENRE_NORMALIZE.get(g, g)
        if normalized in STANDARD_GENRES and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result if result else ["live"]


def infer_genres(title: str, venue: str = "") -> list[str]:
    text = (title + " " + venue).lower()
    found = []

    for genre, keywords in _GENRE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(genre)

    # Venue-based defaults
    for v_key, v_genres in _VENUE_GENRES.items():
        if v_key in text:
            for g in v_genres:
                if g not in found:
                    found.append(g)

    # Fallback
    if not found:
        found = ["live"]

    return found
