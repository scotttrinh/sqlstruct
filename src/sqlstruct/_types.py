"""Python type annotation to SQLAlchemy column type mapping."""

from __future__ import annotations

import datetime
import decimal
import enum
import types
import uuid
from typing import Annotated, Any, Union, get_args, get_origin

import sqlalchemy as sa
from sqlalchemy.types import TypeEngine

from sqlstruct._field import FieldInfo

_SIMPLE_TYPE_MAP: dict[type[Any], type[TypeEngine[Any]]] = {
    bool: sa.Boolean,
    int: sa.Integer,
    float: sa.Float,
    bytes: sa.LargeBinary,
    datetime.datetime: sa.DateTime,
    datetime.date: sa.Date,
    datetime.time: sa.Time,
    datetime.timedelta: sa.Interval,
    decimal.Decimal: sa.Numeric,
    uuid.UUID: sa.Uuid,
}


def unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """Unwrap Annotated and Optional/Union[T, None] into (inner_type, nullable)."""
    origin = get_origin(annotation)
    if origin is Annotated:
        annotation = get_args(annotation)[0]
        origin = get_origin(annotation)

    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        non_none = [arg for arg in args if arg is not type(None)]
        is_nullable = len(non_none) < len(args)
        if len(non_none) == 1:
            inner, inner_nullable = unwrap_optional(non_none[0])
            return inner, is_nullable or inner_nullable
        return annotation, is_nullable

    return annotation, False


def get_sqlalchemy_type(
    annotation: Any, field_info: FieldInfo | None = None
) -> tuple[TypeEngine[Any] | type[TypeEngine[Any]], bool]:
    """Resolve a Python type annotation to a SQLAlchemy type and nullability."""
    inner_type, is_nullable = unwrap_optional(annotation)

    if inner_type is str:
        max_length = field_info.max_length if field_info is not None else None
        return (sa.String(length=max_length) if max_length else sa.String), is_nullable

    if inner_type in _SIMPLE_TYPE_MAP:
        return _SIMPLE_TYPE_MAP[inner_type], is_nullable

    if isinstance(inner_type, type) and issubclass(inner_type, enum.Enum):
        return sa.Enum(inner_type), is_nullable

    origin = get_origin(inner_type)
    if inner_type in (dict, list) or origin in (dict, list):
        return sa.JSON, is_nullable

    raise TypeError(
        f"Unsupported field type {annotation!r} for SQLStruct column mapping. "
        "Pass an explicit sa_column=Column(...) via Field()."
    )
