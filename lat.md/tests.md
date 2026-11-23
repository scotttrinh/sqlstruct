---
lat:
  require-code-mention: true
---
# Tests

Test specifications for sqlstruct, anchored to [[tests/test_sqlstruct.py]] and [[tests/test_e2e_sqlite.py]].

## Package import

Verify that `sqlstruct` imports cleanly and exposes `__all__`.

## End-to-end SQLite CRUD

Verify full insert, select, update, and delete lifecycle against a local SQLite database.

## msgspec JSON round-trip

Verify `msgspec.json.decode`, `msgspec.convert`, and `msgspec.json.encode` interoperability with `SQLStruct` models before and after DB persistence and attribute mutation.

## Foreign keys and joins

Verify `Field(foreign_key=...)` table relationships and multi-entity `select(Hero, Team).join(...)` queries via `Session.exec()`.

## Column metadata and rich types

Verify index creation, unique constraint enforcement, `sa_column` overrides, `UUID`, `Enum`, and `datetime` round-tripping in SQLite.
