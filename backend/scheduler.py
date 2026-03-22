import importlib
import json
import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db import get_db, upsert_event

logger = logging.getLogger(__name__)
_scheduler = None


def run_all_scrapers():
    logger.info("Starting scraper run...")

    scrapers_dir = os.path.join(os.path.dirname(__file__), "scrapers")
    scraper_names = [
        f[:-3]
        for f in sorted(os.listdir(scrapers_dir))
        if f.endswith(".py") and not f.startswith("_") and f != "base.py"
    ]

    total_inserted = 0

    for name in scraper_names:
        try:
            module = importlib.import_module(f"scrapers.{name}")
            logger.info(f"Running scraper: {name}")
            events = module.scrape()

            inserted = 0
            with get_db() as conn:
                for event in events or []:
                    try:
                        if upsert_event(conn, event, name):
                            inserted += 1
                    except Exception as e:
                        logger.error(f"[{name}] Failed to insert event: {e}")

                conn.execute(
                    "INSERT INTO scraper_logs (source, status, message, events_found) VALUES (?, ?, ?, ?)",
                    (name, "success", f"Inserted {inserted} of {len(events or [])} events", len(events or [])),
                )

            total_inserted += inserted
            logger.info(f"[{name}] Done — {inserted} new events")

        except Exception as e:
            logger.error(f"[{name}] Scraper failed: {e}")
            try:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO scraper_logs (source, status, message, events_found) VALUES (?, ?, ?, ?)",
                        (name, "error", str(e)[:500], 0),
                    )
            except Exception:
                pass

    logger.info(f"Scraper run complete — {total_inserted} new events total")
    return total_inserted


def start_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            run_all_scrapers,
            trigger=IntervalTrigger(hours=6),
            id="scrape_events",
            name="Scrape Istanbul events every 6 hours",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("APScheduler started (6-hour interval)")
