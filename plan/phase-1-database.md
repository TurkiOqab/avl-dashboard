# Phase 1 — Database layer

**Deliverable:** `src/db.py` with a `Database` class that owns the SQLite connection, creates the schema, does atomic `import_report`, detects duplicates via `find_report_by_hash`, and supports cascade `delete_report`. All DB behavior is covered by tests.

**Files created:** `src/db.py`, `tests/conftest.py`, `tests/test_db.py`.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated.

---

## Task 1.1: Schema + connection

- [ ] **Step 1: Write the shared `db` fixture and the first failing test**

Path: `tests/conftest.py`

```python
import pytest

from src.db import Database


@pytest.fixture
def db():
    """Fresh in-memory SQLite database per test."""
    d = Database(":memory:")
    d.init_schema()
    yield d
    d.close()
```

Path: `tests/test_db.py`

```python
def test_init_schema_creates_reports_and_records_tables(db):
    cur = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cur.fetchall()]
    assert "reports" in tables
    assert "records" in tables
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db.py -v
```

Expected: FAIL with `ImportError` for `src.db`.

- [ ] **Step 3: Implement `src/db.py`**

Path: `src/db.py`

```python
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    report_date DATE NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    row_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    vehicle_type TEXT NOT NULL,
    plate_number TEXT NOT NULL,
    record_date DATE NOT NULL,
    visits_count INTEGER NOT NULL,
    location_indices TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_records_plate ON records(plate_number);
CREATE INDEX IF NOT EXISTS idx_records_date  ON records(record_date);
"""


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
```

- [ ] **Step 4: Run test to verify pass**

```bash
pytest tests/test_db.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/db.py tests/conftest.py tests/test_db.py
git commit -m "feat(db): Database class with schema init"
```

---

## Task 1.2: Atomic `import_report`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_db.py`:

```python
from datetime import date
import pytest


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
```

- [ ] **Step 2: Run tests to verify failures**

```bash
pytest tests/test_db.py -v
```

Expected: both new tests FAIL with `AttributeError: 'Database' object has no attribute 'import_report'`.

- [ ] **Step 3: Add `import_report` to `src/db.py`**

Append to the `Database` class in `src/db.py`:

```python
    def import_report(
        self,
        filename: str,
        report_date,
        file_hash: str,
        records: list[dict],
    ) -> int:
        try:
            cur = self.conn.execute(
                """
                INSERT INTO reports (filename, report_date, file_hash, row_count)
                VALUES (?, ?, ?, ?)
                """,
                (filename, report_date.isoformat(), file_hash, len(records)),
            )
            report_id = cur.lastrowid
            self.conn.executemany(
                """
                INSERT INTO records (
                    report_id, vehicle_type, plate_number,
                    record_date, visits_count, location_indices
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        report_id,
                        r["vehicle_type"],
                        r["plate_number"],
                        r["record_date"].isoformat(),
                        r["visits_count"],
                        r.get("location_indices"),
                    )
                    for r in records
                ],
            )
            self.conn.commit()
            return report_id
        except Exception:
            self.conn.rollback()
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: all three tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/db.py tests/test_db.py
git commit -m "feat(db): atomic import_report"
```

---

## Task 1.3: Duplicate-hash detection

- [ ] **Step 1: Write failing tests**

Append to `tests/test_db.py`:

```python
import sqlite3


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
```

- [ ] **Step 2: Run tests to verify failures**

```bash
pytest tests/test_db.py -v
```

Expected: the two `find_report_by_hash` tests FAIL; `test_duplicate_file_hash_raises` PASSES already (UNIQUE constraint in schema).

- [ ] **Step 3: Add `find_report_by_hash` to `src/db.py`**

Append to the `Database` class in `src/db.py`:

```python
    def find_report_by_hash(self, file_hash: str):
        return self.conn.execute(
            "SELECT * FROM reports WHERE file_hash = ?", (file_hash,)
        ).fetchone()
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pytest tests/test_db.py -v
```

Expected: all DB tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/db.py tests/test_db.py
git commit -m "feat(db): find_report_by_hash + verify UNIQUE hash"
```

---

## Task 1.4: Cascade delete

- [ ] **Step 1: Write failing test**

Append to `tests/test_db.py`:

```python
def test_delete_report_cascades_to_records(db):
    rid = db.import_report(
        filename="x.xlsx",
        report_date=date(2026, 4, 22),
        file_hash="h-del",
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
    db.delete_report(rid)
    assert db.conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0
    assert db.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/test_db.py::test_delete_report_cascades_to_records -v
```

Expected: FAIL with `AttributeError: ... has no attribute 'delete_report'`.

- [ ] **Step 3: Add `delete_report` to `src/db.py`**

Append to the `Database` class in `src/db.py`:

```python
    def delete_report(self, report_id: int) -> None:
        self.conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        self.conn.commit()
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/test_db.py -v
```

Expected: all DB tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/db.py tests/test_db.py
git commit -m "feat(db): delete_report with cascade"
```
