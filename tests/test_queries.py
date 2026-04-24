from datetime import date

import pytest

from src.queries import get_kpis, get_trend, get_top_vehicles, get_type_breakdown, get_raw


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


def test_trend_per_day_by_type(seeded_db):
    trend = get_trend(seeded_db.conn, _full_filters(), bucket="day")
    rows = sorted(trend, key=lambda r: (r["date"], r["vehicle_type"]))
    assert rows == [
        {"date": date(2026, 4, 21), "vehicle_type": "Sedan", "visits": 2},
        {"date": date(2026, 4, 21), "vehicle_type": "Van",   "visits": 5},
        {"date": date(2026, 4, 22), "vehicle_type": "Sedan", "visits": 3},
        {"date": date(2026, 4, 22), "vehicle_type": "Van",   "visits": 1},
    ]


def test_top_vehicles_sorted_desc(seeded_db):
    top = get_top_vehicles(seeded_db.conn, _full_filters(), limit=10)
    assert top[0]["plate_number"] == "B-2"
    assert top[0]["total_visits"] == 6       # 5+1
    assert top[1]["plate_number"] == "A-1"
    assert top[1]["total_visits"] == 5       # 2+3


def test_type_breakdown(seeded_db):
    bd = get_type_breakdown(seeded_db.conn, _full_filters())
    mapped = {r["vehicle_type"]: r["total_visits"] for r in bd}
    assert mapped == {"Sedan": 5, "Van": 6}


def test_raw_rows_descending_by_date(seeded_db):
    raw = get_raw(seeded_db.conn, _full_filters())
    assert len(raw) == 4
    assert raw[0]["record_date"] == date(2026, 4, 22)
    expected_keys = {
        "record_date", "vehicle_type", "plate_number",
        "visits_count", "location_indices",
    }
    assert expected_keys.issubset(raw[0].keys())
