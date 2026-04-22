# AVL Dashboard

Personal tool to ingest daily Excel off-route reports from an AVL/GPS tracking system, accumulate the history in a local SQLite database, and browse it as an interactive dashboard.

See [`plan/design.md`](plan/design.md) for the full design and [`plan/README.md`](plan/README.md) for the phase index.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501.

## Test

```bash
pytest -v
```
