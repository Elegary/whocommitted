from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime

import pytest

from whocommitted.models import Identity, Role
from whocommitted.ordering import Group
from whocommitted.output import OutputFormat, render


@pytest.fixture
def identities() -> list[Identity]:
    return [
        Identity(
            email="alice@x.io",
            names={"Alice": 3, "Ali": 1},
            roles={Role.COMMITTER, Role.AUTHOR},
            commits={"a", "b"},
            first_seen=datetime(2020, 1, 1, tzinfo=UTC),
            last_seen=datetime(2024, 5, 6, tzinfo=UTC),
        ),
        Identity(email="bob@x.io", roles={Role.CO_AUTHOR}, commits={"c"}),
    ]


def run(identities: list[Identity], fmt: OutputFormat) -> str:
    return run_groups([Group(None, identities)], fmt)


def run_groups(groups: list[Group], fmt: OutputFormat) -> str:
    stream = io.StringIO()
    render(groups, fmt, stream)
    return stream.getvalue()


@pytest.fixture
def groups(identities: list[Identity]) -> list[Group]:
    return [Group("x.io", identities), Group("y.io", [Identity(email="c@y.io", commits={"a"})])]


def test_json(identities: list[Identity]) -> None:
    data = json.loads(run(identities, OutputFormat.JSON))
    assert data[0] == {
        "email": "alice@x.io",
        "name": "Alice",
        "names": ["Ali", "Alice"],
        "domain": "x.io",
        "roles": ["author", "committer"],
        "commits": 2,
        "first_seen": "2020-01-01T00:00:00+00:00",
        "last_seen": "2024-05-06T00:00:00+00:00",
    }
    assert data[1]["first_seen"] is None
    assert data[1]["name"] == ""


def test_csv(identities: list[Identity]) -> None:
    rows = list(csv.DictReader(io.StringIO(run(identities, OutputFormat.CSV))))
    assert rows[0]["names"] == "Ali; Alice"
    assert rows[0]["roles"] == "author; committer"
    assert rows[1]["roles"] == "co-author"


def test_txt(identities: list[Identity]) -> None:
    assert run(identities, OutputFormat.TXT) == "alice@x.io\tAlice\nbob@x.io\t\n"


def test_table(identities: list[Identity]) -> None:
    out = run(identities, OutputFormat.TABLE)
    assert "2 email(s) found" in out
    assert "alice@x.io" in out
    assert "2024-05-06" in out


def test_grouped_json(groups: list[Group]) -> None:
    data = json.loads(run_groups(groups, OutputFormat.JSON))
    assert [(g["group"], g["emails"], g["commits"]) for g in data] == [
        ("x.io", 2, 3),
        ("y.io", 1, 1),
    ]
    assert data[0]["identities"][0]["email"] == "alice@x.io"


def test_grouped_csv(groups: list[Group]) -> None:
    rows = list(csv.DictReader(io.StringIO(run_groups(groups, OutputFormat.CSV))))
    assert [(r["group"], r["email"]) for r in rows] == [
        ("x.io", "alice@x.io"),
        ("x.io", "bob@x.io"),
        ("y.io", "c@y.io"),
    ]


def test_grouped_txt(groups: list[Group]) -> None:
    assert run_groups(groups, OutputFormat.TXT) == (
        "# x.io (2 email(s), 3 commit(s))\n"
        "alice@x.io\tAlice\nbob@x.io\t\n"
        "\n# y.io (1 email(s), 1 commit(s))\n"
        "c@y.io\t\n"
    )


def test_grouped_table(groups: list[Group]) -> None:
    out = run_groups(groups, OutputFormat.TABLE)
    assert "3 email(s) in 2 group(s)" in out
    assert "y.io - 1 email(s), 1 commit(s)" in out
