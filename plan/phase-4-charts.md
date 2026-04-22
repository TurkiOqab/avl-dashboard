# Phase 4 — Charts

**Deliverable:** `src/charts.py` exposes three Plotly figure builders:

- `trend_chart(rows)` — stacked area over time, one series per vehicle type
- `top_vehicles_chart(rows)` — bar chart of plate numbers sorted by total visits
- `type_breakdown_chart(rows)` — donut of visits share by vehicle type

Each function takes the plain list-of-dicts shape returned by Phase 3 queries and returns a `plotly.graph_objects.Figure`. No DB access inside this module.

**Files created:** `src/charts.py`, `tests/test_charts.py`.

Tests are smoke tests only (figure has expected traces / values). Visual correctness is verified manually in the browser during Phase 5.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated.

---

## Task 4.1: Chart builders

- [ ] **Step 1: Write failing smoke tests**

Path: `tests/test_charts.py`

```python
from datetime import date

from src.charts import (
    top_vehicles_chart,
    trend_chart,
    type_breakdown_chart,
)


def test_trend_chart_has_one_trace_per_type():
    data = [
        {"date": date(2026, 4, 21), "vehicle_type": "Sedan", "visits": 2},
        {"date": date(2026, 4, 22), "vehicle_type": "Sedan", "visits": 3},
        {"date": date(2026, 4, 21), "vehicle_type": "Van",   "visits": 5},
    ]
    fig = trend_chart(data)
    trace_names = {t.name for t in fig.data}
    assert trace_names == {"Sedan", "Van"}


def test_top_vehicles_chart_orders_bars_as_given():
    data = [
        {"plate_number": "A", "vehicle_type": "Sedan", "total_visits": 10, "last_seen": "2026-04-22"},
        {"plate_number": "B", "vehicle_type": "Van",   "total_visits": 5,  "last_seen": "2026-04-22"},
    ]
    fig = top_vehicles_chart(data)
    assert list(fig.data[0].x) == ["A", "B"]
    assert list(fig.data[0].y) == [10, 5]


def test_type_breakdown_chart_pie_values():
    data = [
        {"vehicle_type": "Sedan", "total_visits": 5},
        {"vehicle_type": "Van",   "total_visits": 6},
    ]
    fig = type_breakdown_chart(data)
    assert list(fig.data[0].labels) == ["Sedan", "Van"]
    assert list(fig.data[0].values) == [5, 6]
```

- [ ] **Step 2: Run tests to verify failure**

```bash
pytest tests/test_charts.py -v
```

Expected: FAIL with `ImportError` for `src.charts`.

- [ ] **Step 3: Implement `src/charts.py`**

Path: `src/charts.py`

```python
from collections import defaultdict

import plotly.graph_objects as go


def trend_chart(rows: list[dict]) -> go.Figure:
    by_type: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        by_type[r["vehicle_type"]].append((r["date"], r["visits"]))

    fig = go.Figure()
    for vtype, points in by_type.items():
        points.sort()
        fig.add_trace(go.Scatter(
            x=[p[0] for p in points],
            y=[p[1] for p in points],
            mode="lines+markers",
            name=vtype,
            stackgroup="one",
        ))
    fig.update_layout(
        title="Off-route visits over time",
        xaxis_title="Date",
        yaxis_title="Visits",
    )
    return fig


def top_vehicles_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure(data=[go.Bar(
        x=[r["plate_number"] for r in rows],
        y=[r["total_visits"] for r in rows],
        text=[r["vehicle_type"] for r in rows],
    )])
    fig.update_layout(
        title="Top vehicles by off-route visits",
        xaxis_title="Plate",
        yaxis_title="Total visits",
    )
    return fig


def type_breakdown_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=[r["vehicle_type"] for r in rows],
        values=[r["total_visits"] for r in rows],
        hole=0.4,
    )])
    fig.update_layout(title="Share of visits by vehicle type")
    return fig
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/test_charts.py -v
```

Expected: all chart tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat(charts): trend, top vehicles, type breakdown"
```
