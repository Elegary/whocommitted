from __future__ import annotations

import pytest

from whocommitted.filters import apply_filters, build_filters, has_domain, is_bot, is_noreply
from whocommitted.models import Identity


def ident(email: str, *names: str) -> Identity:
    return Identity(email=email, names=dict.fromkeys(names, 1))


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("123+octo@users.noreply.github.com", True),
        ("noreply@github.com", True),
        ("no-reply@example.com", True),
        ("alice@example.com", False),
    ],
)
def test_is_noreply(email: str, expected: bool) -> None:
    assert is_noreply(ident(email)) is expected


@pytest.mark.parametrize(
    ("identity", "expected"),
    [
        (ident("49699333+dependabot[bot]@users.noreply.github.com"), True),
        (ident("x@y.z", "renovate[bot]"), True),
        (ident("ci-bot@corp.io"), True),
        (ident("bot@corp.io"), True),
        (ident("abbott@corp.io", "Abbott"), False),
        (ident("robotics@corp.io"), False),
    ],
)
def test_is_bot(identity: Identity, expected: bool) -> None:
    assert is_bot(identity) is expected


def test_has_domain() -> None:
    assert has_domain(ident("a@corp.io"), ["corp.io"])
    assert has_domain(ident("a@eu.corp.io"), ["corp.io"])
    assert not has_domain(ident("a@notcorp.io"), ["corp.io"])


def test_build_and_apply_filters() -> None:
    ids = [
        ident("a@corp.io"),
        ident("b@other.io"),
        ident("noreply@github.com"),
        ident("ci-bot@corp.io"),
    ]
    assert apply_filters(ids, build_filters()) == ids
    kept = apply_filters(
        ids, build_filters(no_noreply=True, no_bots=True, domains=["@Corp.io", " "])
    )
    assert [i.email for i in kept] == ["a@corp.io"]
