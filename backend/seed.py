"""
Seed the database with realistic sample Istanbul events.
Run once: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, get_db, upsert_event

SAMPLE_EVENTS = [
    {
        "title": "Recondite Live",
        "venue": "Klein",
        "date": "2026-04-05T22:00",
        "genres": ["electronic", "ambient", "techno"],
        "city": "Istanbul",
        "ticket_url": "https://www.kleinistanbul.com",
        "image_url": "https://images.unsplash.com/photo-1571266028243-d220c6a7f2d7?w=800&q=80",
        "source_url": "https://www.kleinistanbul.com/events/recondite",
    },
    {
        "title": "Solomun",
        "venue": "Bonus Parkorman",
        "date": "2026-04-12T23:00",
        "genres": ["house", "deep-house", "electronic", "dj-set"],
        "city": "Istanbul",
        "ticket_url": "https://www.parkorman.com",
        "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800&q=80",
        "source_url": "https://www.parkorman.com/events/solomun",
    },
    {
        "title": "ARTBAT",
        "venue": "Zorlu PSM",
        "date": "2026-04-18T22:30",
        "genres": ["techno", "electronic", "dj-set"],
        "city": "Istanbul",
        "ticket_url": "https://www.zorlu.com.tr",
        "image_url": "https://images.unsplash.com/photo-1574169208507-84376144848b?w=800&q=80",
        "source_url": "https://www.zorlu.com.tr/etkinlikler/artbat",
    },
    {
        "title": "Nils Frahm",
        "venue": "Salon IKSV",
        "date": "2026-04-22T20:00",
        "genres": ["classical", "ambient", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.iksv.org/salonIKSV",
        "image_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=800&q=80",
        "source_url": "https://www.iksv.org/salonIKSV/nilsfrahm",
    },
    {
        "title": "Khruangbin",
        "venue": "Volkswagen Arena",
        "date": "2026-04-25T21:00",
        "genres": ["indie", "world-music", "live", "alternative"],
        "city": "Istanbul",
        "ticket_url": "https://www.volkswagenarenanistanbul.com",
        "image_url": "https://images.unsplash.com/photo-1501612780327-45045538702b?w=800&q=80",
        "source_url": "https://www.volkswagenarenanistanbul.com/khruangbin",
    },
    {
        "title": "İstanbul Caz Gecesi",
        "venue": "Nardis Jazz Club",
        "date": "2026-04-15T21:30",
        "genres": ["jazz", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.nardis.com.tr",
        "image_url": "https://images.unsplash.com/photo-1511192336575-5a79af67a629?w=800&q=80",
        "source_url": "https://www.nardis.com.tr/program",
    },
    {
        "title": "Burial Live AV",
        "venue": "Blind",
        "date": "2026-05-02T23:00",
        "genres": ["electronic", "ambient", "techno"],
        "city": "Istanbul",
        "ticket_url": "https://www.blindistanbul.com",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80",
        "source_url": "https://www.blindistanbul.com/events/burial",
    },
    {
        "title": "Gece Yarısı Punk Festivali",
        "venue": "Dorock XL",
        "date": "2026-04-20T20:00",
        "genres": ["rock", "alternative", "live", "festival"],
        "city": "Istanbul",
        "ticket_url": "https://www.dorock.com.tr",
        "image_url": "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?w=800&q=80",
        "source_url": "https://www.dorock.com.tr/punk-festival",
    },
    {
        "title": "Massive Attack",
        "venue": "KüçükÇiftlik Park",
        "date": "2026-05-10T21:00",
        "genres": ["electronic", "alternative", "ambient", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.kucukciftlikpark.com.tr",
        "image_url": "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800&q=80",
        "source_url": "https://www.kucukciftlikpark.com.tr/massive-attack",
    },
    {
        "title": "Metronomy",
        "venue": "Babylon Bomonti",
        "date": "2026-04-30T21:30",
        "genres": ["indie", "alternative", "pop", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.jollyjoker.com.tr",
        "image_url": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=800&q=80",
        "source_url": "https://www.jollyjoker.com.tr/metronomy",
    },
    {
        "title": "Boiler Room Istanbul",
        "venue": "Klein",
        "date": "2026-05-03T22:00",
        "genres": ["electronic", "techno", "house", "dj-set"],
        "city": "Istanbul",
        "ticket_url": "https://boilerroom.tv",
        "image_url": "https://images.unsplash.com/photo-1598387993441-a364f854cfba?w=800&q=80",
        "source_url": "https://boilerroom.tv/istanbul",
    },
    {
        "title": "İstanbul Devlet Senfoni Orkestrası",
        "venue": "İş Sanat",
        "date": "2026-04-17T19:30",
        "genres": ["classical", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.issanat.com.tr",
        "image_url": "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?w=800&q=80",
        "source_url": "https://www.issanat.com.tr/program",
    },
    {
        "title": "The Blaze",
        "venue": "Zorlu PSM",
        "date": "2026-05-08T21:00",
        "genres": ["electronic", "house", "ambient", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.zorlu.com.tr",
        "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80",
        "source_url": "https://www.zorlu.com.tr/etkinlikler/the-blaze",
    },
    {
        "title": "Peggy Gou",
        "venue": "Bonus Parkorman",
        "date": "2026-05-15T22:00",
        "genres": ["house", "electronic", "dj-set"],
        "city": "Istanbul",
        "ticket_url": "https://www.parkorman.com",
        "image_url": "https://images.unsplash.com/photo-1571079520814-c2840ce6ec7b?w=800&q=80",
        "source_url": "https://www.parkorman.com/peggy-gou",
    },
    {
        "title": "Ceza",
        "venue": "Volkswagen Arena",
        "date": "2026-04-26T20:00",
        "genres": ["hip-hop", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.volkswagenarenanistanbul.com",
        "image_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800&q=80",
        "source_url": "https://www.volkswagenarenanistanbul.com/ceza",
    },
    {
        "title": "Foals",
        "venue": "IF Performance Hall",
        "date": "2026-05-06T21:00",
        "genres": ["indie", "rock", "alternative", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.ifperformancehall.com",
        "image_url": "https://images.unsplash.com/photo-1524368535928-5b5e00ddc76b?w=800&q=80",
        "source_url": "https://www.ifperformancehall.com/foals",
    },
    {
        "title": "Richie Hawtin",
        "venue": "Blind",
        "date": "2026-05-09T23:00",
        "genres": ["techno", "electronic", "dj-set"],
        "city": "Istanbul",
        "ticket_url": "https://www.blindistanbul.com",
        "image_url": "https://images.unsplash.com/photo-1574169208507-84376144848b?w=800&q=80",
        "source_url": "https://www.blindistanbul.com/richie-hawtin",
    },
    {
        "title": "Arkaoda Canlı Gecesi",
        "venue": "Arkaoda",
        "date": "2026-04-19T21:00",
        "genres": ["indie", "alternative", "live"],
        "city": "Istanbul",
        "ticket_url": "https://arkaoda.com",
        "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800&q=80",
        "source_url": "https://arkaoda.com/etkinlikler",
    },
    {
        "title": "Sezen Aksu Akustik",
        "venue": "Harbiye Açıkhava",
        "date": "2026-06-15T20:30",
        "genres": ["pop", "acoustic", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.biletix.com",
        "image_url": "https://images.unsplash.com/photo-1508700929628-666bc8bd84ea?w=800&q=80",
        "source_url": "https://www.biletix.com/sezen-aksu",
    },
    {
        "title": "Floating Points",
        "venue": "Zorlu PSM",
        "date": "2026-05-20T21:30",
        "genres": ["electronic", "jazz", "ambient", "live"],
        "city": "Istanbul",
        "ticket_url": "https://www.zorlu.com.tr",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80",
        "source_url": "https://www.zorlu.com.tr/floating-points",
    },
]


def seed():
    init_db()
    inserted = 0
    with get_db() as conn:
        for event in SAMPLE_EVENTS:
            if upsert_event(conn, event, "seed"):
                inserted += 1
    print(f"Seeded {inserted} events (of {len(SAMPLE_EVENTS)} total)")


if __name__ == "__main__":
    seed()
