# AVL Dashboard — Plan

Personal Streamlit app that ingests daily Excel off-route reports from an AVL/GPS tracking system, accumulates the history in a local SQLite database, and serves an interactive dashboard (KPIs, trends, vehicle rankings) for the operator and management.

Single-user, runs locally on the operator's machine. No cloud, no login.

---

## How to read this folder

- [`design.md`](design.md) — the full design spec (goals, data model, upload flow, dashboard contents, project structure)
- `phase-*.md` — detailed implementation plans, one file per phase

---

## Phases

| # | Phase | Deliverable |
|---|---|---|
| 0 | [Project setup](phase-0-setup.md) | Scaffolding, deps installed, pytest runs |
| 1 | [Database layer](phase-1-database.md) | `Database` class with atomic `import_report`, hash-based dedup, cascade delete |
| 2 | [Excel parser](phase-2-parser.md) | `parse_report` extracts rows into a `ParsedReport`, stops at the photo section |
| 3 | [Dashboard queries](phase-3-queries.md) | KPI, trend, top-vehicles, type-breakdown, raw queries with filter support |
| 4 | [Charts](phase-4-charts.md) | Plotly figure builders for the three dashboard charts |
| 5 | [Streamlit app](phase-5-app.md) | App shell, Upload page (drag-and-drop, preview, save), Dashboard page (filters, KPIs, charts, CSV export) |

Each phase is self-contained: tests pass and the relevant capability works at the end of every phase.

---

## Execution

Work phase-by-phase. Inside each phase, execute tasks in order. Every task uses the same TDD rhythm:

1. Write the failing test
2. Run it; see it fail
3. Write the minimal implementation
4. Run it; see it pass
5. Commit

Commands throughout assume:

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
```

## Tech stack

Python 3.11+, Streamlit, pandas, openpyxl, sqlite3 (stdlib), Plotly, pytest.
