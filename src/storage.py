import os

from src.db import Database

DB_PATH = os.environ.get("AVL_DB_PATH", "data/avl.db")


def get_database() -> Database:
    """Open the shared production database and ensure the schema exists."""
    db = Database(DB_PATH)
    db.init_schema()
    return db
