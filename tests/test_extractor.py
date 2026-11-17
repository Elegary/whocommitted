from __future__ import annotations

from datetime import UTC, datetime

import pytest

from whocommitted.extractor import aggregate, parse_record, parse_trailer
from whocommitted.git import FIELD_SEP, TRAILER_SEP
from whocommitted.models import Commit, Role, Signature


def record(*fields: str) -> str:
    return "\n" + FIELD_SEP.join(fields)


def test_parse_record_with_trailers() -> None:
    trailers = TRAILER_SEP.join(["Bob <bob@x.io>", "broken trailer", "Eve <>"])
    commit = parse_record(
        record(
            "abc",
            "Alice",
            "alice@x.io",
            "2024-01-02T03:04:05+00:00",
            "Carol",
            "carol@x.io",
            "not-a-date",
            trailers,
        )
    )
    assert commit is not None
    assert commit.sha == "abc"
    assert [(s.name, s.email, s.role) for s in commit.signatures] == [
        ("Alice", "alice@x.io", Role.AUTHOR),
        ("Carol", "carol@x.io", Role.COMMITTER),
        ("Bob", "bob@x.io", Role.CO_AUTHOR),
    ]
    assert commit.signatures[0].date == datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert commit.signatures[1].date is None
    assert commit.signatures[2].date == commit.signatures[0].date


def test_parse_record_too_short() -> None:
    assert parse_record("abc\x1fAlice") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Bob <bob@x.io>", ("Bob", "bob@x.io")),
        ("  Bob Smith   <bob@x.io>  ", ("Bob Smith", "bob@x.io")),
        ("<anon@x.io>", ("", "anon@x.io")),
        ("Bob", None),
        ("Bob < >", None),
    ],
)
def test_parse_trailer(value: str, expected: tuple[str, str] | None) -> None:
    assert parse_trailer(value) == expected


def test_aggregate_merges_case_insensitively_and_skips_empty() -> None:
    d1 = datetime(2020, 1, 1, tzinfo=UTC)
    d2 = datetime(2022, 1, 1, tzinfo=UTC)
    commits = [
        Commit("1", (Signature("Alice", "Alice@X.io", Role.AUTHOR, d2),)),
        Commit("2", (Signature("Ali", "alice@x.io", Role.COMMITTER, d1),)),
        Commit("3", (Signature("Alice", "alice@x.io", Role.AUTHOR, None),)),
        Commit("4", (Signature("Nobody", "  ", Role.AUTHOR, d1),)),
    ]
    (alice,) = aggregate(commits)
    assert alice.email == "alice@x.io"
    assert alice.name == "Alice"
    assert alice.names == {"Alice": 2, "Ali": 1}
    assert alice.roles == {Role.AUTHOR, Role.COMMITTER}
    assert alice.commit_count == 3
    assert (alice.first_seen, alice.last_seen) == (d1, d2)
