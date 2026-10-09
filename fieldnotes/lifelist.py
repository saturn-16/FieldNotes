"""SQLite life list storage and weekly goal tracking for Field Notes."""

from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

from fieldnotes.config import DB_PATH
from fieldnotes.models import Detection


def get_db_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Initialize database schema with species and sightings tables."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS species (
                common_name TEXT PRIMARY KEY,
                scientific_name TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                place TEXT,
                note TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                common_name TEXT NOT NULL,
                scientific_name TEXT NOT NULL,
                seen_at TEXT NOT NULL,
                place TEXT,
                confidence REAL NOT NULL
            )
            """
        )
    conn.close()


def add_sightings(
    detections: list[Detection],
    place: str | None,
    when: datetime,
    db_path: Path | str = DB_PATH,
) -> list[str]:
    """Record sightings and add new birds to life list.

    Returns a list of newly discovered species common names.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    new_species: list[str] = []
    seen_time_str = when.isoformat()
    place_str = place.strip() if place and place.strip() else None

    with conn:
        for det in detections:
            # Check if species already exists in life list
            cur = conn.execute(
                "SELECT 1 FROM species WHERE common_name = ?",
                (det.common_name,),
            )
            exists = cur.fetchone() is not None

            if not exists and det.common_name not in new_species:
                conn.execute(
                    """
                    INSERT INTO species (common_name, scientific_name, first_seen, place, note)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        det.common_name,
                        det.scientific_name,
                        seen_time_str,
                        place_str,
                        "",
                    ),
                )
                new_species.append(det.common_name)

            # Always log sighting
            conn.execute(
                """
                INSERT INTO sightings (common_name, scientific_name, seen_at, place, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    det.common_name,
                    det.scientific_name,
                    seen_time_str,
                    place_str,
                    det.confidence,
                ),
            )

    conn.close()
    return new_species


def get_life_list(db_path: Path | str = DB_PATH) -> list[sqlite3.Row]:
    """Retrieve full life list sorted by first seen descending."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cur = conn.execute(
        """
        SELECT common_name, scientific_name, first_seen, place, note
        FROM species
        ORDER BY first_seen DESC, common_name ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def weekly_progress(goal: int = 5, db_path: Path | str = DB_PATH) -> tuple[int, int]:
    """Calculate the number of new species recorded during the current calendar week.

    Returns (count_new_this_week, goal).
    """
    init_db(db_path)
    now = datetime.now()
    # Monday of the current week at 00:00:00
    start_of_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_str = start_of_week.isoformat()

    conn = get_db_connection(db_path)
    cur = conn.execute(
        "SELECT COUNT(*) as count FROM species WHERE first_seen >= ?",
        (start_str,),
    )
    row = cur.fetchone()
    count = row["count"] if row else 0
    conn.close()
    return count, goal
