"""Core SQLStruct base class and metaclass bridging msgspec.Struct and SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, dataclass_transform, get_type_hints

import msgspec
import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, MetaData, Table, event
from sqlalchemy.orm import Mapper, configure_mappers, registry
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from sqlstruct._field import _UNSET, Field, FieldInfo
from sqlstruct._types import get_sqlalchemy_type

_default_registry = registry()


def _init_sa_state(obj: Any) -> None:
    """Populate __dict__ from msgspec C slots and attach SQLAlchemy InstanceState."""
    cls = obj.__class__
    mgr = getattr(cls, "_sa_class_manager", None)
    if mgr is None or "_sa_instance_state" in obj.__dict__:
        return
    struct_members: dict[str, Any] = getattr(cls, "_struct_members", {})
    for name, desc in struct_members.items():
        obj.__dict__[name] = desc.__get__(obj, cls)
    mgr.setup_instance(obj)


def _sync_dict_to_struct(target: Any, *args: Any) -> None:
    """Copy SQLAlchemy-populated __dict__ values back into msgspec C struct slots."""
    cls = target.__class__
    struct_members: dict[str, Any] = getattr(cls, "_struct_members", {})
    for name, desc in struct_members.items():
        if name in target.__dict__:
            desc.__set__(target, target.__dict__[name])


def _make_attr_set_listener(desc: Any) -> Any:
    def _on_set(target: Any, value: Any, oldvalue: Any, initiator: Any) -> None:
        if value is not NO_VALUE and value is not NEVER_SET:
            desc.__set__(target, value)

    return _on_set


def _build_column(name: str, annotation: Any, field_info: FieldInfo) -> Column[Any]:
    """Build a SQLAlchemy Column from a field name, annotation, and FieldInfo."""
    if field_info.sa_column is not None:
        col = field_info.sa_column
        if not col.name:
            col.name = name
        if not col.key:
            col.key = name
        return col

    sa_type, is_optional = get_sqlalchemy_type(annotation, field_info)
    col_args: list[Any] = []
    if field_info.foreign_key is not None:
        fk_kwargs: dict[str, Any] = {}
        if field_info.ondelete is not None:
            fk_kwargs["ondelete"] = field_info.ondelete
        col_args.append(ForeignKey(field_info.foreign_key, **fk_kwargs))

    if field_info.sa_column_args:
        col_args.extend(field_info.sa_column_args)

    if field_info.nullable is not None:
        nullable = field_info.nullable
    elif field_info.primary_key:
        nullable = False
    else:
        nullable = is_optional

    col_kwargs: dict[str, Any] = {
        "primary_key": field_info.primary_key,
        "index": field_info.index,
        "unique": field_info.unique,
        "nullable": nullable,
    }
    if field_info.sa_column_kwargs:
        col_kwargs.update(field_info.sa_column_kwargs)

    return Column(name, sa_type, *col_args, **col_kwargs)


_StructMetaBase: type[type] = type(msgspec.Struct)


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class SQLStructMeta(_StructMetaBase):  # type: ignore[misc]
    """Metaclass for SQLStruct translating Field() specs and table=True mapping."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        table: bool = False,
        **kwargs: Any,
    ) -> Any:
        kwargs.setdefault("dict", True)
        kwargs.setdefault("weakref", True)
        kwargs.setdefault("kw_only", True)

        extracted: dict[str, FieldInfo] = {}
        for attr_name, attr_val in list(namespace.items()):
            if isinstance(attr_val, FieldInfo):
                extracted[attr_name] = attr_val
                if attr_val.default is not _UNSET:
                    namespace[attr_name] = msgspec.field(default=attr_val.default)
                elif attr_val.default_factory is not _UNSET:
                    namespace[attr_name] = msgspec.field(
                        default_factory=attr_val.default_factory
                    )
                else:
                    del namespace[attr_name]

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        merged_fields: dict[str, FieldInfo] = {}
        for base in reversed(cls.__mro__):
            base_fields = getattr(base, "__sqlstruct_fields__", None)
            if base_fields:
                merged_fields.update(base_fields)
        merged_fields.update(extracted)
        cls_any: Any = cls
        cls_any.__sqlstruct_fields__ = merged_fields

        if table:
            mcs._configure_table(cls)

        return cls

    @staticmethod
    def _configure_table(cls: Any) -> None:
        tablename = cls.__dict__.get("__tablename__") or cls.__name__.lower()
        hints = get_type_hints(cls, include_extras=True)
        field_infos: dict[str, FieldInfo] = cls.__sqlstruct_fields__

        columns = [
            _build_column(
                field_name,
                hints[field_name],
                field_infos.get(field_name, FieldInfo()),
            )
            for field_name in cls.__struct_fields__
        ]

        sa_table = Table(tablename, cls.metadata, *columns)

        # Save msgspec C member_descriptors and remove them so SQLAlchemy can
        # install InstrumentedAttribute descriptors on the class.
        struct_members: dict[str, Any] = {}
        for field_name in cls.__struct_fields__:
            struct_members[field_name] = getattr(cls, field_name)
            if field_name in cls.__dict__:
                delattr(cls, field_name)
        cls._struct_members = struct_members

        mapper: Mapper[Any] = cls._sa_registry.map_imperatively(cls, sa_table)
        configure_mappers()

        cls.__table__ = sa_table
        cls.__mapper__ = mapper

        # SQLAlchemy's default ClassManager.new_instance calls cls.__new__(cls),
        # which raises TypeError on msgspec.Struct C types. Construct via
        # StructMeta.__call__ directly with placeholder Nones instead.
        struct_fields: tuple[str, ...] = cls.__struct_fields__

        def _new_instance(state: Any = None) -> Any:
            return _StructMetaBase.__call__(cls, **dict.fromkeys(struct_fields, None))

        cls._sa_class_manager.new_instance = _new_instance

        event.listen(cls, "load", _sync_dict_to_struct)
        event.listen(cls, "refresh", _sync_dict_to_struct)
        for field_name, desc in struct_members.items():
            event.listen(getattr(cls, field_name), "set", _make_attr_set_listener(desc))

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        obj = super().__call__(*args, **kwargs)
        _init_sa_state(obj)
        return obj


class SQLStruct(
    msgspec.Struct,
    metaclass=SQLStructMeta,
    dict=True,
    weakref=True,
    kw_only=True,
):
    """Base class for msgspec-backed SQLAlchemy models and schemas."""

    _sa_registry: ClassVar[registry] = _default_registry
    metadata: ClassVar[MetaData] = _default_registry.metadata
    __sqlstruct_fields__: ClassVar[dict[str, FieldInfo]] = {}
    __table__: ClassVar[sa.Table]
    __mapper__: ClassVar[Mapper[Any]]

    if TYPE_CHECKING:

        def __init_subclass__(cls, *, table: bool = False, **kwargs: Any) -> None: ...

    def __post_init__(self) -> None:
        _init_sa_state(self)
