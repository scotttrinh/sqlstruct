"""Pytest configuration and shared SQLite fixtures."""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


class _PurePythonSQLAlchemyCyFinder(importlib.abc.MetaPathFinder):
    """Work around SQLAlchemy 2.1.9 Cython _cache_key_cy segfault on Python 3.15.0b2."""

    def find_spec(
        self, fullname: str, path: Any, target: Any = None
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname.startswith("sqlalchemy.") and fullname.endswith("_cy"):
            import sqlalchemy

            base = os.path.dirname(sqlalchemy.__file__)
            py_path = os.path.join(base, *fullname.split(".")[1:]) + ".py"
            if os.path.exists(py_path):
                return importlib.util.spec_from_file_location(fullname, py_path)
        return None


if sys.version_info[:2] == (3, 15) and "sqlalchemy" not in sys.modules:
    sys.meta_path.insert(0, _PurePythonSQLAlchemyCyFinder())

from sqlstruct import Session, SQLStruct, create_engine  # noqa: E402


@pytest.fixture
def sqlite_engine(tmp_path: Path) -> Iterator[Any]:
    """Create a fresh file-backed SQLite engine per test and create all tables."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLStruct.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session(sqlite_engine: Any) -> Iterator[Session]:
    """Yield an open Session bound to the per-test SQLite engine."""
    with Session(sqlite_engine) as sess:
        yield sess
