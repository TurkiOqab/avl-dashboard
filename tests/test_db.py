def test_init_schema_creates_reports_and_records_tables(db):
    cur = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cur.fetchall()]
    assert "reports" in tables
    assert "records" in tables
