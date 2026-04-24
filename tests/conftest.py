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
