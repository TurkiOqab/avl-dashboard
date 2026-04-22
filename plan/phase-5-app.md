# Phase 5 — Streamlit app

**Deliverable:** a working Streamlit app with two pages, backed by the shared SQLite database.

- `app.py` — entry/landing page
- `src/storage.py` — helper that opens the production DB (gitignored `data/avl.db`)
- `pages/1_Upload.py` — drop an `.xlsx`, see preview, save (with hash-based dedup)
- `pages/2_Dashboard.py` — filter bar, KPIs, trend chart, ranking bar, type donut, raw table with CSV export

End state: `streamlit run app.py` serves the full application, all pytest tests pass, and the repo is pushed to GitHub.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated.

---

## Task 5.1: App shell + shared storage

- [ ] **Step 1: Create `src/storage.py`**

Path: `src/storage.py`

```python
import os

from src.db import Database

DB_PATH = os.environ.get("AVL_DB_PATH", "data/avl.db")


def get_database() -> Database:
    """Open the shared production database and ensure the schema exists."""
    db = Database(DB_PATH)
    db.init_schema()
    return db
```

- [ ] **Step 2: Create `app.py`**

Path: `app.py`

```python
import streamlit as st

st.set_page_config(
    page_title="AVL Dashboard",
    page_icon=":vertical_traffic_light:",
    layout="wide",
)

st.title("AVL Dashboard")
st.markdown(
    """
Personal tool for off-route report analysis.

- **Upload**: import a daily Excel report.
- **Dashboard**: filter, chart, and export the accumulated history.

Use the sidebar to navigate.
"""
)
```

- [ ] **Step 3: Verify the app boots**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
streamlit run app.py --server.headless true &
STREAMLIT_PID=$!
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
kill $STREAMLIT_PID
```

Expected: `200`.

- [ ] **Step 4: Commit**

```bash
git add app.py src/storage.py
git commit -m "feat(app): Streamlit entry point + shared DB helper"
```

---

## Task 5.2: Upload page

- [ ] **Step 1: Implement the upload page**

Path: `pages/1_Upload.py`

```python
import hashlib
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st

from src.parser import parse_report
from src.storage import get_database


st.set_page_config(page_title="Upload", layout="wide")
st.title("Upload a daily report")

uploaded = st.file_uploader(
    "Drop an Excel (.xlsx) report here",
    type=["xlsx"],
    accept_multiple_files=False,
)

if uploaded is not None:
    raw = uploaded.getvalue()
    file_hash = hashlib.sha256(raw).hexdigest()

    db = get_database()
    existing = db.find_report_by_hash(file_hash)
    if existing is not None:
        st.warning(
            f"Already imported on {existing['uploaded_at']} as "
            f"`{existing['filename']}`."
        )
        st.stop()

    try:
        parsed = parse_report(BytesIO(raw))
    except Exception as exc:
        st.error(f"Could not parse this file: {exc}")
        st.stop()

    st.success(
        f"Parsed **{len(parsed.records)}** rows "
        f"(report date: **{parsed.report_date}**)."
    )
    df = pd.DataFrame(parsed.records)
    st.dataframe(df, use_container_width=True)

    if st.button("Save to database", type="primary"):
        try:
            db.import_report(
                filename=uploaded.name,
                report_date=parsed.report_date,
                file_hash=file_hash,
                records=parsed.records,
            )
            st.success("Saved. Go to the Dashboard to view it.")
        except sqlite3.IntegrityError:
            st.error("This file was imported between page loads. Refresh.")
```

- [ ] **Step 2: Manually verify**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
streamlit run app.py
```

In the browser: sidebar → **Upload**, drop a real `.xlsx` report. Verify preview renders and **Save** persists.

Note: if the headers in your real file don't match the defaults in
`src/parser.HEADERS`, the parser will raise "Missing required column".
Edit `HEADERS` to match (e.g. if the AVL portal uses Arabic labels), then
re-upload.

- [ ] **Step 3: Commit**

```bash
git add pages/1_Upload.py
git commit -m "feat(upload): drag-and-drop .xlsx with preview + dedup"
```

---

## Task 5.3: Dashboard page

- [ ] **Step 1: Implement the dashboard page**

Path: `pages/2_Dashboard.py`

```python
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.charts import (
    top_vehicles_chart,
    trend_chart,
    type_breakdown_chart,
)
from src.queries import (
    get_kpis,
    get_raw,
    get_top_vehicles,
    get_trend,
    get_type_breakdown,
)
from src.storage import get_database


st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard")

db = get_database()

all_types = [r[0] for r in db.conn.execute(
    "SELECT DISTINCT vehicle_type FROM records ORDER BY vehicle_type"
).fetchall()]
all_plates = [r[0] for r in db.conn.execute(
    "SELECT DISTINCT plate_number FROM records ORDER BY plate_number"
).fetchall()]

if not all_types:
    st.info("No data yet. Upload a report on the Upload page first.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
with c1:
    start = st.date_input("From", value=date.today() - timedelta(days=30))
with c2:
    end = st.date_input("To", value=date.today())
with c3:
    types = st.multiselect("Vehicle type", all_types, default=all_types)
with c4:
    plates = st.multiselect("Plate", all_plates, default=[])

filters = {
    "start_date": start,
    "end_date": end,
    "vehicle_types": types or None,
    "plate_numbers": plates or None,
}

kpis = get_kpis(db.conn, filters)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total visits", kpis["total_visits"])
k2.metric("Active vehicles", kpis["active_vehicles"])
k3.metric("Avg per vehicle", f"{kpis['avg_visits_per_vehicle']:.1f}")
k4.metric("Worst day", str(kpis["worst_day"] or "—"))

bucket = "week" if (end - start).days > 60 else "day"
st.plotly_chart(
    trend_chart(get_trend(db.conn, filters, bucket=bucket)),
    use_container_width=True,
)

left, right = st.columns([2, 1])
with left:
    st.plotly_chart(
        top_vehicles_chart(get_top_vehicles(db.conn, filters, limit=10)),
        use_container_width=True,
    )
with right:
    st.plotly_chart(
        type_breakdown_chart(get_type_breakdown(db.conn, filters)),
        use_container_width=True,
    )

st.subheader("Per-vehicle summary")
summary_df = pd.DataFrame(get_top_vehicles(db.conn, filters, limit=1000))
st.dataframe(summary_df, use_container_width=True)

st.subheader("Raw records")
raw_df = pd.DataFrame(get_raw(db.conn, filters))
st.dataframe(raw_df, use_container_width=True)
st.download_button(
    "Export CSV",
    data=raw_df.to_csv(index=False).encode(),
    file_name=f"avl-records-{start}-to-{end}.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Manually verify**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
streamlit run app.py
```

Sidebar → **Dashboard**. Verify:

- KPI cards show non-zero numbers.
- Trend, ranking, and donut all render.
- Filters (date range, type, plate) update KPIs and charts.
- **Export CSV** downloads a file containing the expected rows.

- [ ] **Step 3: Commit**

```bash
git add pages/2_Dashboard.py
git commit -m "feat(dashboard): filters, KPIs, charts, raw table, CSV export"
```

---

## Task 5.4: Final verification + push

- [ ] **Step 1: Full test suite**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
pytest -v
```

Expected: every test passes.

- [ ] **Step 2: End-to-end manual smoke test**

```bash
streamlit run app.py
```

Checklist:

1. Home page loads.
2. Upload page accepts an `.xlsx`, shows preview, and saves.
3. Re-uploading the same file is rejected as duplicate.
4. Dashboard page shows KPIs + all three charts + raw table.
5. Filters change both KPIs and charts.
6. CSV export downloads a file with the expected rows.

- [ ] **Step 3: Push to GitHub**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
git push origin main
```

Open https://github.com/TurkiOqab/avl-dashboard and confirm `main` has all the phase commits.
