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
