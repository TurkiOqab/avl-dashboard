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
