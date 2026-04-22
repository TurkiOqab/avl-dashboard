# Phase 2 — Excel parser

**Deliverable:** `src/parser.py` with a pure `parse_report(source)` function that reads an `.xlsx` file and returns a `ParsedReport(report_date, records)`. Header names are in a configurable `HEADERS` constant. Parser stops at the first empty row so the photo section is ignored.

**Files created:** `src/parser.py`, `tests/test_parser.py`. Extends `tests/conftest.py` with a synthetic-Excel fixture.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated.

---

## Task 2.1: Happy path

- [ ] **Step 1: Extend `tests/conftest.py` with a synthetic-Excel fixture**

Append to `tests/conftest.py`:

```python
from openpyxl import Workbook

from src.parser import HEADERS


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
```

- [ ] **Step 2: Write failing test**

Path: `tests/test_parser.py`

```python
from datetime import date

from src.parser import parse_report


def test_parse_report_extracts_all_rows(make_excel):
    rows = [
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
    ]
    path = make_excel(rows)
    parsed = parse_report(path)

    assert parsed.report_date == date(2026, 4, 22)
    assert len(parsed.records) == 2
    assert parsed.records[0]["plate_number"] == "ABC-1234"
    assert parsed.records[0]["visits_count"] == 3
    assert parsed.records[0]["location_indices"] == "12, 13, 14"
    assert parsed.records[0]["record_date"] == date(2026, 4, 22)
```

- [ ] **Step 3: Run test to verify failure**

```bash
pytest tests/test_parser.py -v
```

Expected: FAIL with `ImportError` for `src.parser`.

- [ ] **Step 4: Implement `src/parser.py`**

Path: `src/parser.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import BinaryIO, Union

from openpyxl import load_workbook


# Header names as they appear in the source Excel file.
# Update these to match your AVL report (e.g. Arabic labels).
HEADERS = {
    "vehicle_type": "Type",
    "plate_number": "Plate Number",
    "record_date": "Date",
    "visits_count": "Number of Locations Visited",
    "location_indices": "Location Index Number",
}


@dataclass
class ParsedReport:
    report_date: date
    records: list[dict]


def parse_report(source: Union[str, Path, BinaryIO]) -> ParsedReport:
    wb = load_workbook(source, data_only=True, read_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise ValueError("Empty workbook.")

    col_index = _build_column_index(header_row)

    records: list[dict] = []
    for row in rows_iter:
        if _is_empty(row):
            break  # end of data / start of photo section
        records.append({
            "vehicle_type": _str(row[col_index["vehicle_type"]]),
            "plate_number": _str(row[col_index["plate_number"]]),
            "record_date": _as_date(row[col_index["record_date"]]),
            "visits_count": int(row[col_index["visits_count"]] or 0),
            "location_indices": _str(row[col_index["location_indices"]]),
        })

    if not records:
        raise ValueError("No data rows found in the report.")

    report_date = max(r["record_date"] for r in records)
    return ParsedReport(report_date=report_date, records=records)


def _build_column_index(header_row) -> dict:
    normalized = [_normalize(h) for h in header_row]
    idx = {}
    for key, name in HEADERS.items():
        target = _normalize(name)
        if target not in normalized:
            raise ValueError(f"Missing required column: '{name}'")
        idx[key] = normalized.index(target)
    return idx


def _normalize(s) -> str:
    return "" if s is None else str(s).strip().lower()


def _str(v) -> str:
    return "" if v is None else str(v).strip()


def _as_date(v) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    raise ValueError(f"Cannot interpret {v!r} as a date.")


def _is_empty(row) -> bool:
    return all(c is None or (isinstance(c, str) and c.strip() == "") for c in row)
```

- [ ] **Step 5: Run test to verify pass**

```bash
pytest tests/test_parser.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/parser.py tests/test_parser.py tests/conftest.py
git commit -m "feat(parser): parse Excel into ParsedReport"
```

---

## Task 2.2: Edge cases

- [ ] **Step 1: Add three edge-case tests**

Append to `tests/test_parser.py`:

```python
import pytest
from openpyxl import Workbook


def test_missing_header_raises(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Wrong1", "Wrong2", "Wrong3", "Wrong4", "Wrong5"])
    path = tmp_path / "bad.xlsx"
    wb.save(path)

    with pytest.raises(ValueError, match="Missing required column"):
        parse_report(path)


def test_no_data_rows_raises(make_excel):
    path = make_excel([])
    with pytest.raises(ValueError, match="No data rows"):
        parse_report(path)


def test_empty_row_terminates_parsing(make_excel):
    """An empty row marks end-of-data. Everything below (the photo section)
    must be ignored."""
    rows = [
        {
            "vehicle_type": "Sedan",
            "plate_number": "ABC-1234",
            "record_date": date(2026, 4, 22),
            "visits_count": 2,
            "location_indices": "1, 2",
        }
    ]
    path = make_excel(rows, filename="with-photos.xlsx")

    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    ws.append([None, None, None, None, None])
    ws.append(["PHOTO SECTION", None, None, None, None])
    ws.append(["Photo 1", None, None, None, None])
    wb.save(path)

    parsed = parse_report(path)
    assert len(parsed.records) == 1
    assert parsed.records[0]["plate_number"] == "ABC-1234"
```

- [ ] **Step 2: Run tests to verify all pass**

```bash
pytest tests/test_parser.py -v
```

Expected: all four parser tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_parser.py
git commit -m "test(parser): missing header, empty data, photo-section termination"
```
