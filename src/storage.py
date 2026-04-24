import os

import streamlit as st

from src.db import Database

DB_PATH = os.environ.get("AVL_DB_PATH", "data/avl.db")


@st.cache_resource
def get_database() -> Database:
    """Open the shared production database and ensure the schema exists.

    Cached with st.cache_resource so Streamlit reuses the same connection
    across reruns (every widget interaction triggers a rerun, and opening a
    fresh sqlite connection each time would be wasteful)."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    db = Database(DB_PATH)
    db.init_schema()
    return db
