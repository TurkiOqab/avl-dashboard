from datetime import date

import pytest
from openpyxl import Workbook

from src.db import Database
from src.parser import HEADERS


@pytest.fixture
def db():
    """Fresh in-memory SQLite database per test."""
    d = Database(":memory:")
    d.init_schema()
    yield d
    d.close()


def _write_excel(path, rows):
    wb = Workbook()
    ws = wb.active
    ws.append([
        HEADERS["vehicle_type"],
        HEADERS["plate_number"],
        HEADERS["record_date"],
        HEADERS["visits_count"],
        HEADERS["location_indices"],
    ])
    for r in rows:
        ws.append([
            r["vehicle_type"],
            r["plate_number"],
            r["record_date"],
            r["visits_count"],
            r["location_indices"],
        ])
    wb.save(path)
    return path


@pytest.fixture
def make_excel(tmp_path):
    def _inner(rows, filename="sample.xlsx"):
        return _write_excel(tmp_path / filename, rows)
    return _inner


@pytest.fixture
def seeded_db(db):
    """DB pre-populated with a known two-day / two-vehicle dataset."""
    db.import_report(
        filename="day1.xlsx",
        report_date=date(2026, 4, 21),
        file_hash="h1",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "A-1", "record_date": date(2026, 4, 21), "visits_count": 2, "location_indices": "1,2"},
            {"vehicle_type": "Van",   "plate_number": "B-2", "record_date": date(2026, 4, 21), "visits_count": 5, "location_indices": "3,4,5,6,7"},
        ],
    )
    db.import_report(
        filename="day2.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="h2",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "A-1", "record_date": date(2026, 4, 22), "visits_count": 3, "location_indices": "8,9,10"},
            {"vehicle_type": "Van",   "plate_number": "B-2", "record_date": date(2026, 4, 22), "visits_count": 1, "location_indices": "11"},
        ],
    )
    return db
