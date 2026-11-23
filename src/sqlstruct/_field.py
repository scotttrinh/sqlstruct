"""Field descriptor and metadata for SQLStruct models."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import Column

_UNSET: Any = object()


class FieldInfo:
    """Metadata describing a SQLStruct field and its SQLAlchemy column options."""

    def __init__(
        self,
        default: Any = _UNSET,
        *,
        default_factory: Callable[[], Any] | Any = _UNSET,
        primary_key: bool = False,
        foreign_key: str | None = None,
        ondelete: str | None = None,
        index: bool = False,
        unique: bool = False,
        nullable: bool | None = None,
        max_length: int | None = None,
        sa_column: Column[Any] | None = None,
        sa_column_args: tuple[Any, ...] | None = None,
        sa_column_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.default = default
        self.default_factory = default_factory
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.ondelete = ondelete
        self.index = index
        self.unique = unique
        self.nullable = nullable
        self.max_length = max_length
        self.sa_column = sa_column
        self.sa_column_args = sa_column_args
        self.sa_column_kwargs = sa_column_kwargs


def Field(
    default: Any = _UNSET,
    *,
    default_factory: Callable[[], Any] | Any = _UNSET,
    primary_key: bool = False,
    foreign_key: str | None = None,
    ondelete: str | None = None,
    index: bool = False,
    unique: bool = False,
    nullable: bool | None = None,
    max_length: int | None = None,
    sa_column: Column[Any] | None = None,
    sa_column_args: tuple[Any, ...] | None = None,
    sa_column_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Declare a field on a SQLStruct with optional SQLAlchemy column metadata."""
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        primary_key=primary_key,
        foreign_key=foreign_key,
        ondelete=ondelete,
        index=index,
        unique=unique,
        nullable=nullable,
        max_length=max_length,
        sa_column=sa_column,
        sa_column_args=sa_column_args,
        sa_column_kwargs=sa_column_kwargs,
    )
