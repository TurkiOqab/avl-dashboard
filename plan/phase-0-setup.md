# Phase 0 — Project setup

**Deliverable:** directory scaffold, dependencies installed, pytest collects with zero tests.

**Files created:** `.gitignore`, `requirements.txt`, `README.md`, `src/__init__.py`, `tests/__init__.py`, `pages/`, `data/.gitkeep`.

Commands assume you are at `/Users/turkioqab/Projects/avl-dashboard` with the venv activated once it exists.

---

## Task 0.1: Scaffold files

- [ ] **Step 1: Write `.gitignore`**

Path: `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.venv/
venv/

# Data
data/*.db
data/*.db-journal

# Editor
.DS_Store
.vscode/
.idea/
```

- [ ] **Step 2: Write `requirements.txt`**

Path: `requirements.txt`

```
streamlit==1.39.0
pandas==2.2.3
openpyxl==3.1.5
plotly==5.24.1
pytest==8.3.3
```

- [ ] **Step 3: Write `README.md`**

Path: `README.md`

````markdown
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
````

- [ ] **Step 4: Create package and data directories**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
mkdir -p src tests pages data
touch src/__init__.py tests/__init__.py data/.gitkeep
```

- [ ] **Step 5: Create venv and install deps**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 6: Verify pytest runs (0 tests collected)**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
source .venv/bin/activate
pytest
```

Expected: exit code 5 with `no tests ran` — acceptable at this stage.

- [ ] **Step 7: Commit**

```bash
cd /Users/turkioqab/Projects/avl-dashboard
git add .gitignore requirements.txt README.md src tests pages data
git commit -m "chore: project scaffold (deps, gitignore, dirs)"
```
