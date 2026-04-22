# Phase 3 — Dashboard queries

**Deliverable:** `src/queries.py` exposes read-only queries that take a `sqlite3.Connection` + a filter dict and return dashboard-ready data:

- `get_kpis(conn, filters)` → `{total_visits, active_vehicles, avg_visits_per_vehicle, worst_day}`
- `get_trend(conn, filters, bucket="day")` → list of `{date, vehicle_type, visits}`
- `get_top_vehicles(conn, filters, limit=10)` → list of `{plate_number, vehicle_type, total_visits, last_seen}`
- `get_type_breakdown(conn, filters)` → list of `{vehicle_type, total_visits}`
- `get_raw(conn, filters)` → list of `{record_date, vehicle_type, plate_number, visits_count, location_indices}`

**Filter dict shape:**
```python
{
    "start_date": date,
    "end_date": date,
    "vehicle_types": list[str] | None,  # None = all
    "plate_numbers": list[str] | None,  # None = all
}
```

**Files created:** `src/queries.py`, `tests/test_queries.py`. Extends `tests/conftest.py` with a seeded fixture.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated.

---

## Task 3.1: Filter clause + KPIs

- [ ] **Step 1: Add a `seeded_db` fixture**

Append to `tests/conftest.py`:

```python
from datetime import date as _date


@pytest.fixture
def seeded_db(db):
    """DB pre-populated with a known two-day / two-vehicle dataset."""
    db.import_report(
        filename="day1.xlsx",
        report_date=_date(2026, 4, 21),
        file_hash="h1",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "A-1", "record_date": _date(2026, 4, 21), "visits_count": 2, "location_indices": "1,2"},
            {"vehicle_type": "Van",   "plate_number": "B-2", "record_date": _date(2026, 4, 21), "visits_count": 5, "location_indices": "3,4,5,6,7"},
        ],
    )
    db.import_report(
        filename="day2.xlsx",
        report_date=_date(2026, 4, 22),
        file_hash="h2",
        records=[
            {"vehicle_type": "Sedan", "plate_number": "A-1", "record_date": _date(2026, 4, 22), "visits_count": 3, "location_indices": "8,9,10"},
            {"vehicle_type": "Van",   "plate_number": "B-2", "record_date": _date(2026, 4, 22), "visits_count": 1, "location_indices": "11"},
        ],
    )
    return db
```

- [ ] **Step 2: Write failing KPI tests**

Path: `tests/test_queries.py`

```python
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
```

- [ ] **Step 3: Run tests to verify failure**

```bash
pytest tests/test_queries.py -v
```

Expected: FAIL with `ImportError` for `src.queries`.

- [ ] **Step 4: Implement `src/queries.py`**

Path: `src/queries.py`

```python
from datetime import date
from sqlite3 import Connection


def _where_clause(filters: dict) -> tuple[str, list]:
    clauses = ["record_date BETWEEN ? AND ?"]
    params: list = [
        filters["start_date"].isoformat(),
        filters["end_date"].isoformat(),
    ]
    if filters.get("vehicle_types"):
        placeholders = ",".join("?" * len(filters["vehicle_types"]))
        clauses.append(f"vehicle_type IN ({placeholders})")
        params.extend(filters["vehicle_types"])
    if filters.get("plate_numbers"):
        placeholders = ",".join("?" * len(filters["plate_numbers"]))
        clauses.append(f"plate_number IN ({placeholders})")
        params.extend(filters["plate_numbers"])
    return " AND ".join(clauses), params


def get_kpis(conn: Connection, filters: dict) -> dict:
    where, params = _where_clause(filters)
    total = conn.execute(
        f"SELECT COALESCE(SUM(visits_count), 0) FROM records WHERE {where}",
        params,
    ).fetchone()[0]
    active = conn.execute(
        f"SELECT COUNT(DISTINCT plate_number) FROM records WHERE {where}",
        params,
    ).fetchone()[0]
    avg = (total / active) if active else 0.0
    worst = conn.execute(
        f"""
        SELECT record_date FROM records
        WHERE {where}
        GROUP BY record_date
        ORDER BY SUM(visits_count) DESC, record_date DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    worst_day = date.fromisoformat(worst[0]) if worst else None
    return {
        "total_visits": total,
        "active_vehicles": active,
        "avg_visits_per_vehicle": avg,
        "worst_day": worst_day,
    }
```

- [ ] **Step 5: Run tests to verify pass**

```bash
pytest tests/test_queries.py -v
```

Expected: all three KPI tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/queries.py tests/test_queries.py tests/conftest.py
git commit -m "feat(queries): KPIs with filter support"
```

---

## Task 3.2: Trend, top vehicles, type breakdown, raw

- [ ] **Step 1: Write failing tests**

Append to `tests/test_queries.py`:

```python
from src.queries import get_trend, get_top_vehicles, get_type_breakdown, get_raw


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
```

- [ ] **Step 2: Run tests to verify failures**

```bash
pytest tests/test_queries.py -v
```

Expected: the four new tests FAIL with `ImportError`.

- [ ] **Step 3: Extend `src/queries.py`**

Append to `src/queries.py`:

```python
def get_trend(conn: Connection, filters: dict, bucket: str = "day") -> list[dict]:
    if bucket not in {"day", "week"}:
        raise ValueError("bucket must be 'day' or 'week'")
    where, params = _where_clause(filters)
    date_expr = (
        "record_date"
        if bucket == "day"
        # Week = Monday of the ISO week. SQLite 'weekday 0' jumps to next Sunday;
        # stepping back 6 days lands on Monday.
        else "DATE(record_date, 'weekday 0', '-6 days')"
    )
    rows = conn.execute(
        f"""
        SELECT {date_expr} AS d, vehicle_type, SUM(visits_count) AS visits
        FROM records
        WHERE {where}
        GROUP BY d, vehicle_type
        ORDER BY d, vehicle_type
        """,
        params,
    ).fetchall()
    return [
        {
            "date": date.fromisoformat(r["d"]),
            "vehicle_type": r["vehicle_type"],
            "visits": r["visits"],
        }
        for r in rows
    ]


def get_top_vehicles(conn: Connection, filters: dict, limit: int = 10) -> list[dict]:
    where, params = _where_clause(filters)
    rows = conn.execute(
        f"""
        SELECT plate_number, vehicle_type,
               SUM(visits_count) AS total_visits,
               MAX(record_date)  AS last_seen
        FROM records
        WHERE {where}
        GROUP BY plate_number, vehicle_type
        ORDER BY total_visits DESC, plate_number
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()
    return [dict(r) for r in rows]


def get_type_breakdown(conn: Connection, filters: dict) -> list[dict]:
    where, params = _where_clause(filters)
    rows = conn.execute(
        f"""
        SELECT vehicle_type, SUM(visits_count) AS total_visits
        FROM records
        WHERE {where}
        GROUP BY vehicle_type
        ORDER BY total_visits DESC
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def get_raw(conn: Connection, filters: dict) -> list[dict]:
    where, params = _where_clause(filters)
    rows = conn.execute(
        f"""
        SELECT record_date, vehicle_type, plate_number,
               visits_count, location_indices
        FROM records
        WHERE {where}
        ORDER BY record_date DESC, plate_number
        """,
        params,
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["record_date"] = date.fromisoformat(d["record_date"])
        out.append(d)
    return out
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/test_queries.py -v
```

Expected: all query tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/queries.py tests/test_queries.py
git commit -m "feat(queries): trend, top vehicles, type breakdown, raw"
```
