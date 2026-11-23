"""End-to-end tests against a local SQLite database."""

from __future__ import annotations

import datetime
import enum
import uuid

import msgspec
import pytest
from sqlalchemy import Column, String, inspect
from sqlalchemy.exc import IntegrityError

from sqlstruct import Field, Session, SQLStruct, col, select


class Alignment(enum.Enum):
    HERO = "hero"
    VILLAIN = "villain"


class HeroBase(SQLStruct):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)


class Team(SQLStruct, table=True):
    __tablename__ = "team"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    headquarters: str


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")


class AuditRecord(SQLStruct, table=True):
    __tablename__ = "audit_records"

    id: int | None = Field(default=None, primary_key=True)
    external_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    alignment: Alignment = Alignment.HERO
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    )
    notes: str = Field(sa_column=Column(String(120), nullable=False, default=""))


# @lat: [[tests#Tests#End-to-end SQLite CRUD]]
def test_e2e_crud_lifecycle(session: Session) -> None:
    deadpond = Hero(name="Deadpond", secret_name="Dive Wilson")
    spider_boy = Hero(name="Spider-Boy", secret_name="Pedro Parqueador", age=16)

    session.add(deadpond)
    session.add(spider_boy)
    session.commit()
    session.refresh(deadpond)
    session.refresh(spider_boy)

    assert deadpond.id is not None
    assert spider_boy.id is not None

    heroes = session.exec(select(Hero).order_by(col(Hero.id))).all()
    assert len(heroes) == 2
    assert heroes[0].name == "Deadpond"
    assert heroes[1].age == 16

    fetched = session.exec(select(Hero).where(col(Hero.name) == "Spider-Boy")).one()
    fetched.age = 17
    session.add(fetched)
    session.commit()
    session.refresh(fetched)
    assert fetched.age == 17

    session.delete(deadpond)
    session.commit()

    remaining = session.exec(select(Hero)).all()
    assert [h.name for h in remaining] == ["Spider-Boy"]


# @lat: [[tests#Tests#msgspec JSON round-trip]]
def test_e2e_msgspec_json_interop(session: Session) -> None:
    payload = b'{"name": "Rusty-Man", "secret_name": "Tommy Sharp", "age": 48}'
    create_schema = msgspec.json.decode(payload, type=HeroBase)
    assert isinstance(create_schema, HeroBase)
    assert not hasattr(create_schema, "__table__")

    hero = msgspec.convert(msgspec.structs.asdict(create_schema), Hero)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    encoded_after_commit = msgspec.json.encode(hero)
    decoded = msgspec.json.decode(encoded_after_commit)
    assert decoded == {
        "name": "Rusty-Man",
        "secret_name": "Tommy Sharp",
        "age": 48,
        "id": hero.id,
        "team_id": None,
    }

    queried = session.exec(select(Hero).where(col(Hero.id) == hero.id)).one()
    queried.age = 49
    encoded_after_mutation = msgspec.json.encode(queried)
    assert msgspec.json.decode(encoded_after_mutation)["age"] == 49


# @lat: [[tests#Tests#Foreign keys and joins]]
def test_e2e_foreign_key_and_join(session: Session) -> None:
    preventers = Team(name="Preventers", headquarters="Sharp Tower")
    z_force = Team(name="Z-Force", headquarters="Sister Margaret's Bar")
    session.add(preventers)
    session.add(z_force)
    session.commit()
    session.refresh(preventers)
    session.refresh(z_force)

    hero = Hero(
        name="Tarantula",
        secret_name="Natalia Roman-on",
        age=32,
        team_id=preventers.id,
    )
    session.add(hero)
    session.commit()

    rows = session.exec(
        select(Hero, Team).join(Team, col(Hero.team_id) == col(Team.id))
    ).all()
    assert len(rows) == 1
    found_hero, found_team = rows[0]
    assert found_hero.name == "Tarantula"
    assert found_team.name == "Preventers"


# @lat: [[tests#Tests#Column metadata and rich types]]
def test_e2e_column_metadata_and_rich_types(
    sqlite_engine: object, session: Session
) -> None:
    inspector = inspect(sqlite_engine)
    hero_indexes = {idx["name"] for idx in inspector.get_indexes("hero")}
    assert any("name" in name for name in hero_indexes)

    team1 = Team(name="UniqueTeam", headquarters="HQ 1")
    team2 = Team(name="UniqueTeam", headquarters="HQ 2")
    session.add(team1)
    session.commit()
    session.add(team2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    record = AuditRecord(notes="created in test")
    session.add(record)
    session.commit()
    session.refresh(record)

    loaded = session.exec(select(AuditRecord)).one()
    assert isinstance(loaded.external_id, uuid.UUID)
    assert loaded.alignment is Alignment.HERO
    assert loaded.notes == "created in test"
