# Overview

`sqlstruct` brings SQLModel-style ergonomics to `msgspec.Struct` models backed by SQLAlchemy.

## Core Architecture

[[src/sqlstruct/_struct.py#SQLStruct]] subclasses `msgspec.Struct` with [[src/sqlstruct/_struct.py#SQLStructMeta]] to support both plain schema structs (`table=False`) and ORM-mapped tables (`table=True`).

- [[src/sqlstruct/_field.py#Field]] captures SQLAlchemy column options (`primary_key`, `foreign_key`, `index`, `unique`, `nullable`, `max_length`, `sa_column`) alongside `msgspec` defaults.
- [[src/sqlstruct/_types.py#get_sqlalchemy_type]] maps Python and `Optional` / `Annotated` type hints to SQLAlchemy column types.
- [[src/sqlstruct/_session.py#Session]] extends SQLAlchemy's session with `.exec()` for SQLModel-style scalar queries.
- `table=True` models sync values between SQLAlchemy's `__dict__` and `msgspec` C struct slots on instantiation, `load`, `refresh`, and attribute `set` events so `msgspec.json.encode` stays up to date.
