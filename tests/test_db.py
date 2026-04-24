import sqlite3
from datetime import date

import pytest


def test_init_schema_creates_reports_and_records_tables(db):
    cur = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cur.fetchall()]
    assert "reports" in tables
    assert "records" in tables


def test_import_report_inserts_report_and_records(db):
    rid = db.import_report(
        filename="2026-04-22.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="h1",
        records=[
            {
                "vehicle_type": "Sedan",
                "plate_number": "ABC-1234",
                "record_date": date(2026, 4, 22),
                "visits_count": 3,
                "location_indices": "12, 13, 14",
            },
            {
                "vehicle_type": "Van",
                "plate_number": "XYZ-9999",
                "record_date": date(2026, 4, 22),
                "visits_count": 1,
                "location_indices": "7",
            },
        ],
    )
    assert isinstance(rid, int) and rid > 0
    report = db.conn.execute("SELECT * FROM reports WHERE id = ?", (rid,)).fetchone()
    assert report["filename"] == "2026-04-22.xlsx"
    assert report["row_count"] == 2
    record_count = db.conn.execute(
        "SELECT COUNT(*) FROM records WHERE report_id = ?", (rid,)
    ).fetchone()[0]
    assert record_count == 2


def test_import_report_rolls_back_on_bad_record(db):
    """If any record insert fails, the report row must not persist."""
    bad_records = [
        {
            "vehicle_type": "Sedan",
            "plate_number": "ABC-1234",
            "record_date": date(2026, 4, 22),
            "visits_count": 1,
            "location_indices": "1",
        },
        {  # missing visits_count -> KeyError during insert
            "vehicle_type": "Van",
            "plate_number": "XYZ-9999",
            "record_date": date(2026, 4, 22),
            "location_indices": "2",
        },
    ]
    with pytest.raises(KeyError):
        db.import_report(
            filename="bad.xlsx",
            report_date=date(2026, 4, 22),
            file_hash="h-bad",
            records=bad_records,
        )
    assert db.conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0
    assert db.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0


def test_find_report_by_hash_returns_none_when_missing(db):
    assert db.find_report_by_hash("nope") is None


def test_find_report_by_hash_returns_row_when_present(db):
    db.import_report(
        filename="x.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="abc123",
        records=[
            {
                "vehicle_type": "Sedan",
                "plate_number": "A-1",
                "record_date": date(2026, 4, 22),
                "visits_count": 1,
                "location_indices": "1",
            }
        ],
    )
    row = db.find_report_by_hash("abc123")
    assert row is not None
    assert row["filename"] == "x.xlsx"


def test_duplicate_file_hash_raises(db):
    base = dict(
        filename="a.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="dup",
        records=[
            {
                "vehicle_type": "Sedan",
                "plate_number": "A-1",
                "record_date": date(2026, 4, 22),
                "visits_count": 1,
                "location_indices": "1",
            }
        ],
    )
    db.import_report(**base)
    base["filename"] = "b.xlsx"
    with pytest.raises(sqlite3.IntegrityError):
        db.import_report(**base)


def test_delete_report_cascades_to_records(db):
    # Import two reports with records. Deleting only the first must
    # cascade-delete its records and leave the second report's records intact.
    # (A single-report test cannot distinguish cascade from "no rows anyway".)
    rid1 = db.import_report(
        filename="x.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="h-del",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "A-1", "record_date": date(2026, 4, 22), "visits_count": 1, "location_indices": "1"},
            {"vehicle_type": "Van",   "plate_number": "B-2", "record_date": date(2026, 4, 22), "visits_count": 2, "location_indices": "2,3"},
            {"vehicle_type": "Truck", "plate_number": "C-3", "record_date": date(2026, 4, 22), "visits_count": 3, "location_indices": "4,5,6"},
        ],
    )
    db.import_report(
        filename="y.xlsx",
        report_date=date(2026, 4, 23),
        file_hash="h-keep",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "Z-9", "record_date": date(2026, 4, 23), "visits_count": 1, "location_indices": "9"},
        ],
    )

    # Pre-conditions: both reports present, 4 total records, 3 belong to rid1.
    assert db.conn.execute("SELECT COUNT(*) FROM records WHERE report_id = ?", (rid1,)).fetchone()[0] == 3
    assert db.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 4

    db.delete_report(rid1)

    # Post-conditions: rid1 gone, its 3 records cascaded away, but the other
    # report and its 1 record still exist.
    assert db.conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 1
    assert db.conn.execute("SELECT COUNT(*) FROM records WHERE report_id = ?", (rid1,)).fetchone()[0] == 0
    assert db.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 1
