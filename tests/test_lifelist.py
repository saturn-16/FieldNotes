"""Unit tests for lifelist.py (new vs. repeat species, weekly goal progress)."""

from datetime import datetime, timedelta
import sqlite3
import pytest

from fieldnotes.lifelist import add_sightings, get_life_list, weekly_progress, init_db
from fieldnotes.models import Detection


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_lifelist.db"
    init_db(db_file)
    return db_file


def test_add_new_species_and_get_life_list(temp_db):
    detections = [
        Detection("Northern Cardinal", "Cardinalis cardinalis", 0.95, 0.0, 3.0),
        Detection("Blue Jay", "Cyanocitta cristata", 0.88, 3.0, 6.0),
    ]
    when = datetime(2026, 10, 9, 8, 30)
    new_birds = add_sightings(detections, "Backyard", when, db_path=temp_db)

    assert set(new_birds) == {"Northern Cardinal", "Blue Jay"}

    life_list = get_life_list(db_path=temp_db)
    assert len(life_list) == 2
    names = [row["common_name"] for row in life_list]
    assert "Northern Cardinal" in names
    assert "Blue Jay" in names

    # Verify fields
    cardinal = next(r for r in life_list if r["common_name"] == "Northern Cardinal")
    assert cardinal["scientific_name"] == "Cardinalis cardinalis"
    assert cardinal["place"] == "Backyard"
    assert cardinal["first_seen"] == when.isoformat()


def test_repeat_species_not_duplicated_in_life_list(temp_db):
    first_time = datetime(2026, 10, 1, 9, 0)
    add_sightings(
        [Detection("American Robin", "Turdus migratorius", 0.9, 0.0, 3.0)],
        "Meadow",
        first_time,
        db_path=temp_db,
    )

    # Repeat sighting at a later date
    second_time = datetime(2026, 10, 9, 10, 0)
    new_birds = add_sightings(
        [
            Detection("American Robin", "Turdus migratorius", 0.95, 0.0, 3.0),
            Detection("Song Sparrow", "Melospiza melodia", 0.85, 3.0, 6.0),
        ],
        "Lakeside",
        second_time,
        db_path=temp_db,
    )

    # Only Song Sparrow is new
    assert new_birds == ["Song Sparrow"]

    # Life list still contains Robin once (with original first_seen) plus Song Sparrow
    life_list = get_life_list(db_path=temp_db)
    assert len(life_list) == 2
    robin = next(r for r in life_list if r["common_name"] == "American Robin")
    assert robin["first_seen"] == first_time.isoformat()

    # Sightings table logs both encounters
    conn = sqlite3.connect(str(temp_db))
    cur = conn.execute("SELECT COUNT(*) FROM sightings WHERE common_name = 'American Robin'")
    assert cur.fetchone()[0] == 2
    conn.close()


def test_weekly_progress(temp_db):
    now = datetime.now()
    # Add a sighting from today (this week)
    add_sightings(
        [Detection("Black-capped Chickadee", "Poecile atricapillus", 0.9, 0.0, 3.0)],
        "Woods",
        now,
        db_path=temp_db,
    )

    # Add a sighting from 3 weeks ago
    old_time = now - timedelta(days=21)
    add_sightings(
        [Detection("Mourning Dove", "Zenaida macroura", 0.85, 0.0, 3.0)],
        "Patio",
        old_time,
        db_path=temp_db,
    )

    count_this_week, goal = weekly_progress(goal=5, db_path=temp_db)
    assert count_this_week == 1
    assert goal == 5
