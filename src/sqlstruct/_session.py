"""Session and query helpers for SQLStruct."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session as _SASession
from sqlalchemy.sql import Select


def col[T](column_expression: T) -> Mapped[T]:
    """Cast a SQLStruct attribute to a SQLAlchemy Mapped column for type checkers."""
    return cast(Mapped[T], column_expression)


class Session(_SASession):
    """SQLAlchemy Session with a SQLModel-style .exec() helper."""

    def exec(self, statement: Any, **kwargs: Any) -> Any:
        """Execute a statement, returning scalar results for single-entity SELECTs."""
        if isinstance(statement, Select) and len(statement.column_descriptions) == 1:
            return self.scalars(statement, **kwargs)
        return self.execute(statement, **kwargs)


__all__ = ["Session", "col", "create_engine", "select"]
