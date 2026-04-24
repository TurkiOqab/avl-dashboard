from datetime import date

import pytest

from src.queries import get_kpis


def _full_filters():
    return {
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 12, 31),
        "vehicle_types": None,
        "plate_numbers": None,
    }


def test_kpis_totals(seeded_db):
    kpis = get_kpis(seeded_db.conn, _full_filters())
    assert kpis["total_visits"] == 11       # 2+5+3+1
    assert kpis["active_vehicles"] == 2
    assert kpis["avg_visits_per_vehicle"] == pytest.approx(5.5)
    assert kpis["worst_day"] == date(2026, 4, 21)  # 7 vs 4


def test_kpis_respect_plate_filter(seeded_db):
    filters = _full_filters()
    filters["plate_numbers"] = ["A-1"]
    kpis = get_kpis(seeded_db.conn, filters)
    assert kpis["total_visits"] == 5        # 2+3
    assert kpis["active_vehicles"] == 1


def test_kpis_respect_date_range(seeded_db):
    filters = _full_filters()
    filters["start_date"] = date(2026, 4, 22)
    kpis = get_kpis(seeded_db.conn, filters)
    assert kpis["total_visits"] == 4        # day 2 only
    assert kpis["worst_day"] == date(2026, 4, 22)
