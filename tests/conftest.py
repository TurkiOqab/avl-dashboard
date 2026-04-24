import pytest

from src.db import Database


@pytest.fixture
def db():
    """Fresh in-memory SQLite database per test."""
    d = Database(":memory:")
    d.init_schema()
    yield d
    d.close()
