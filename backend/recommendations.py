from collections import Counter
from db import get_db, row_to_dict


def get_recommendations(user_id: int, limit: int = 20) -> list:
    with get_db() as conn:
        # Get user's liked events
        liked_rows = conn.execute(
            """
            SELECT e.* FROM events e
            JOIN likes l ON e.id = l.event_id
            WHERE l.user_id = ?
            """,
            (user_id,),
        ).fetchall()

        if not liked_rows:
            # No likes yet — return upcoming events sorted by date
            rows = conn.execute(
                "SELECT * FROM events ORDER BY date ASC LIMIT ?", (limit,)
            ).fetchall()
            return [row_to_dict(r) for r in rows]

        genre_counter: Counter = Counter()
        venue_counter: Counter = Counter()
        liked_ids: set = set()

        for row in liked_rows:
            e = row_to_dict(row)
            liked_ids.add(e["id"])
            for genre in e.get("genres") or []:
                genre_counter[genre] += 1
            if e.get("venue"):
                venue_counter[e["venue"]] += 1

        # Fetch all events not yet liked
        placeholders = ",".join("?" * len(liked_ids)) if liked_ids else "0"
        all_rows = conn.execute(
            f"SELECT * FROM events WHERE id NOT IN ({placeholders}) ORDER BY date ASC",
            list(liked_ids),
        ).fetchall()

        scored = []
        for row in all_rows:
            e = row_to_dict(row)
            score = 0.0

            for genre in e.get("genres") or []:
                if genre in genre_counter:
                    score += genre_counter[genre] * 0.7

            if e.get("venue") and e["venue"] in venue_counter:
                score += venue_counter[e["venue"]] * 0.3

            scored.append((score, e))

        # Sort by score DESC, then date ASC
        scored.sort(key=lambda x: (-x[0], x[1].get("date") or ""))
        return [e for _, e in scored[:limit]]
