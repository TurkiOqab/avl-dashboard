# AVL Dashboard — Design Spec

**Date:** 2026-04-22
**Status:** Draft
**Author:** Turki Oqab

## 1. Problem

As an AVL operator, I download daily Excel reports from a GPS tracking website and manually review them. Each report lists, for every vehicle on a given day: the vehicle type, its plate number, the date, how many off-route locations it visited, and the index numbers of those locations (which tie to photos embedded elsewhere in the same Excel file).

Reviewing these reports one file at a time makes it hard to see trends (which vehicles are repeat offenders, is the problem getting better or worse, which vehicle types are most problematic). I want a personal tool that ingests these Excel files, accumulates the data into a local history, and presents interactive dashboards I can use personally — and show to management.

## 2. Goals & Non-Goals

### Goals
- Upload daily Excel reports and accumulate them into a queryable history.
- Provide an interactive dashboard with filters, trends, rankings, and KPIs.
- Prevent duplicate imports of the same file.
- Export filtered data for ad-hoc reporting.

### Non-Goals (v1)
- Multi-user / authentication / multi-tenancy. This is a personal tool; SaaS infrastructure is deferred until proven useful.
- Extracting or displaying the photos embedded in the Excel files. The dashboard is numbers-only.
- Mapping / geocoding off-route locations. Locations are identified only by an index number tied to a photo; there is no text name or GPS coordinate to map.
- Cloud hosting. Runs locally on the operator's laptop.
- Automated ingestion / scheduled imports. Upload is manual, on demand.

## 3. Scope

### In scope
- A single Streamlit application with two pages: **Upload** and **Dashboard**.
- A local SQLite database that accumulates records across uploads.
- Excel parsing for the fixed column layout of the source reports.
- Dashboard views: KPI cards, trend line chart, vehicle ranking bar chart, type breakdown, filterable raw-data table with CSV export.

### Out of scope
- Photo extraction or display.
- Geospatial features.
- Any form of login or multi-user support.
- Deployment beyond `streamlit run app.py` on the operator's machine.

## 4. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit app                      │
│                                                     │
│  ┌───────────┐   ┌──────────┐   ┌───────────────┐   │
│  │  Upload   │──▶│  Parser  │──▶│   SQLite DB   │   │
│  │   page    │   │ (pandas+ │   │  (history)    │   │
│  └───────────┘   │ openpyxl)│   └───────┬───────┘   │
│                  └──────────┘           │           │
│                                         ▼           │
│                               ┌─────────────────┐   │
│                               │   Dashboard     │   │
│                               │   (charts,      │   │
│                               │    filters)     │   │
│                               └─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

Three cleanly separated responsibilities:

1. **Parser** — reads an uploaded Excel, extracts rows of (type, plate, date, visits_count, location_indices), ignores the photo section. Pure function, easy to test.
2. **Storage** — SQLite file holds all history. Each upload appends rows, with a file-hash dedup check.
3. **UI** — two Streamlit pages: Upload (drag-and-drop → preview → save) and Dashboard (filters + charts).

Everything runs locally. One command to start. One SQLite file holds all data. No server, no login, no deployment pipeline.

## 5. Data Model

### `reports` table — one row per uploaded Excel file

| Column        | Type        | Notes                              |
|---------------|-------------|------------------------------------|
| `id`          | INTEGER PK  | Auto-increment                     |
| `filename`    | TEXT        | Original filename                  |
| `uploaded_at` | TIMESTAMP   | When the import ran                |
| `report_date` | DATE        | Date the report covers             |
| `file_hash`   | TEXT UNIQUE | SHA-256 of file bytes, for dedup   |
| `row_count`   | INTEGER     | Number of records imported         |

### `records` table — one row per (vehicle, date), mirrors one Excel row

| Column             | Type       | Notes                                            |
|--------------------|------------|--------------------------------------------------|
| `id`               | INTEGER PK | Auto-increment                                   |
| `report_id`        | INTEGER FK | → `reports.id`, cascade delete                   |
| `vehicle_type`     | TEXT       |                                                  |
| `plate_number`     | TEXT       |                                                  |
| `record_date`      | DATE       |                                                  |
| `visits_count`     | INTEGER    | Number of off-route locations visited that day   |
| `location_indices` | TEXT       | Raw indices as stored, e.g. `"12, 13, 14"`       |

**Indexes:** `plate_number`, `record_date` on `records` for fast dashboard filtering.

**Design notes:**
- `file_hash` prevents importing the same file twice.
- `location_indices` is stored as a text blob (not exploded into separate rows) because v1 is numbers-only and doesn't query individual indices.
- Cascade delete on `report_id` so removing a report also removes its records — allows correcting a bad import by deleting and re-uploading.

## 6. Upload & Parse Flow

1. User drops an `.xlsx` file on the Upload page.
2. Compute SHA-256 hash of file bytes.
3. If hash already exists in `reports`, show "Already imported on <date>" and stop.
4. Parse with openpyxl + pandas:
   - Read the main sheet.
   - Detect header row by known column names (case-insensitive).
   - Stop reading at the photo section (detected by empty rows or the start of the photo block).
   - Extract type, plate, date, visits_count, location_indices.
5. Show a preview table: "Found N rows from `<report_date>`. Save?"
6. On confirm, insert into `reports` and `records` in a single transaction.
7. Show success message with a link to the Dashboard.

Assumption (confirmed): every Excel has the **same column layout**, so column names can be hardcoded.

## 7. Dashboard

### Filter bar (top)
- Date range (default: last 30 days)
- Vehicle type (multi-select, default: all)
- Plate number (multi-select, default: all)

### KPI cards
- Total off-route visits in range
- Active vehicles in range
- Average visits per vehicle
- Day with most visits

### Trends over time
- Line chart: total visits per day (or per week if range > 60 days), stacked by vehicle type.

### Vehicle rankings
- Bar chart: top 10 vehicles by total visits (descending).
- Clicking a bar filters the dashboard to that plate.

### Breakdown
- Pie/donut: visits share by vehicle type.
- Table: per-vehicle summary (plate, type, total visits, last seen off-route).

### Raw data
- Filterable table of `records` rows, sorted by date descending.
- "Export to CSV" button for ad-hoc reporting.

## 8. Project Structure

```
avl-dashboard/
├── app.py                 # Streamlit entry point
├── pages/
│   ├── 1_Upload.py
│   └── 2_Dashboard.py
├── src/
│   ├── parser.py          # Excel → list of record dicts (pure function)
│   ├── db.py              # SQLite connection, schema init, CRUD
│   ├── queries.py         # named queries for the dashboard
│   └── charts.py          # reusable chart builders
├── tests/
│   ├── test_parser.py
│   ├── test_db.py
│   └── fixtures/          # small sample Excel files
├── data/
│   └── avl.db             # gitignored
├── requirements.txt
└── README.md
```

Rationale:
- `src/` is the logic layer; `pages/` is thin UI.
- `parser.py` is a pure function — the riskiest piece (file-format quirks), so it must be testable in isolation.
- `queries.py` holds named SQL so the dashboard page stays readable.
- `data/` is gitignored — the real SQLite file never enters git.

## 9. Testing

- **`test_parser.py`** — feed fixture `.xlsx` files, assert the parser extracts expected rows. Highest-priority tests (format bugs hide here).
- **`test_db.py`** — in-memory SQLite. Verify first import works, duplicate import is rejected, report delete cascades.
- **Dashboard** — manually verified by clicking around. Streamlit UI tests are overkill for a personal tool.

## 10. Tech Stack

- **Language:** Python 3.11+
- **UI:** Streamlit
- **Data:** pandas, openpyxl
- **Database:** SQLite (stdlib `sqlite3`)
- **Charts:** Plotly (via Streamlit's native chart support) or Altair
- **Testing:** pytest

## 11. Open Questions

- Exact header names in the source Excel. Will be pinned down during parser development using a real sample file.
- Format of `location_indices` in the source ("12, 13, 14" vs "12-14" vs other). Stored as raw text for now; parser doesn't need to normalize.
- Whether to ever add a "delete report" UI control, or keep deletion as a manual SQL operation in v1. Defaulting to a simple UI control since corrections happen.

## 12. Future (Post-v1)

Things deliberately excluded from v1 but worth recording:
- Photo extraction and gallery view.
- Multi-user / auth / cloud deployment (the "SaaS" framing).
- Scheduled ingestion (watch folder, email import).
- Alerts (e.g., "plate X exceeded N visits this week").
- Mapping, if location text or coordinates ever become available in the source reports.
