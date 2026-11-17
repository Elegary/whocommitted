from __future__ import annotations

from datetime import UTC, datetime

import pytest

from whocommitted.models import Identity
from whocommitted.ordering import GroupBy, SortKey, group_identities, sort_identities


def ident(email: str, name: str, commits: int, year: int | None = None) -> Identity:
    date = datetime(year, 1, 1, tzinfo=UTC) if year else None
    return Identity(
        email=email,
        names={name: 1},
        commits={f"{email}-{n}" for n in range(commits)},
        first_seen=date,
        last_seen=date,
    )


A = ident("zoe@a.io", "zoe", 1, 2020)
B = ident("amy@b.io", "Bob", 5, 2024)
C = ident("carl@a.io", "carl", 5)
D = ident("dan@gmail.com", "Dan", 2, 2022)
ALL = [A, B, C, D]


def emails(identities: list[Identity]) -> list[str]:
    return [i.email for i in identities]


@pytest.mark.parametrize(
    ("keys", "reverse", "expected"),
    [
        ((), False, ["amy@b.io", "carl@a.io", "dan@gmail.com", "zoe@a.io"]),
        ((), True, ["zoe@a.io", "dan@gmail.com", "carl@a.io", "amy@b.io"]),
        ((SortKey.EMAIL,), False, ["amy@b.io", "carl@a.io", "dan@gmail.com", "zoe@a.io"]),
        ((SortKey.NAME,), False, ["amy@b.io", "carl@a.io", "dan@gmail.com", "zoe@a.io"]),
        ((SortKey.COMMITS,), False, ["amy@b.io", "carl@a.io", "dan@gmail.com", "zoe@a.io"]),
        ((SortKey.COMMITS,), True, ["zoe@a.io", "dan@gmail.com", "carl@a.io", "amy@b.io"]),
        ((SortKey.DOMAIN,), False, ["carl@a.io", "zoe@a.io", "amy@b.io", "dan@gmail.com"]),
        (
            (SortKey.DOMAIN, SortKey.COMMITS),
            False,
            ["carl@a.io", "zoe@a.io", "amy@b.io", "dan@gmail.com"],
        ),
        ((SortKey.FIRST_SEEN,), False, ["zoe@a.io", "dan@gmail.com", "amy@b.io", "carl@a.io"]),
        ((SortKey.LAST_SEEN,), False, ["amy@b.io", "dan@gmail.com", "zoe@a.io", "carl@a.io"]),
    ],
)
def test_sort(keys: tuple[SortKey, ...], reverse: bool, expected: list[str]) -> None:
    assert emails(sort_identities(ALL, keys, reverse=reverse)) == expected


def test_group_none() -> None:
    (group,) = group_identities(ALL, GroupBy.NONE)
    assert group.key is None
    assert group.identities == ALL


def test_group_by_domain_alphabetical_keeps_inner_order() -> None:
    ordered = sort_identities(ALL, [SortKey.COMMITS])
    groups = group_identities(ordered, GroupBy.DOMAIN, [SortKey.EMAIL])
    assert [g.key for g in groups] == ["a.io", "b.io", "gmail.com"]
    assert emails(groups[0].identities) == ["carl@a.io", "zoe@a.io"]
    assert groups[0].commit_count == 6


def test_group_by_domain_reverse() -> None:
    groups = group_identities(ALL, GroupBy.DOMAIN, [SortKey.DOMAIN], reverse=True)
    assert [g.key for g in groups] == ["gmail.com", "b.io", "a.io"]


def test_group_order_follows_commits() -> None:
    groups = group_identities(ALL, GroupBy.DOMAIN, [SortKey.COMMITS])
    assert [(g.key, g.commit_count) for g in groups] == [
        ("a.io", 6),
        ("b.io", 5),
        ("gmail.com", 2),
    ]
    reverse = group_identities(ALL, GroupBy.DOMAIN, [SortKey.COMMITS], reverse=True)
    assert [g.key for g in reverse] == ["gmail.com", "b.io", "a.io"]


def test_group_by_kind() -> None:
    bot = ident("ci-bot@a.io", "ci", 1)
    noreply = ident("1+x@users.noreply.github.com", "x", 1)
    groups = group_identities([*ALL, bot, noreply], GroupBy.KIND, [SortKey.EMAIL])
    assert {g.key: emails(g.identities) for g in groups} == {
        "bot": ["ci-bot@a.io"],
        "noreply": ["1+x@users.noreply.github.com"],
        "organization": ["zoe@a.io", "amy@b.io", "carl@a.io"],
        "personal": ["dan@gmail.com"],
    }
