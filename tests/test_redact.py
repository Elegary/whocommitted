from __future__ import annotations

import pytest

from whocommitted.models import Identity, Role
from whocommitted.ordering import Group
from whocommitted.redact import redact_email, redact_groups, redact_identity, redact_name


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("jane.doe@example.com", "j*****e@example.com"),
        ("ab@x.io", "a*****@x.io"),
        ("a@x.io", "a*****@x.io"),
        ("12345678+bob@users.noreply.github.com", "1*****b@users.noreply.github.com"),
        ("no-at-sign", "n*****n"),
    ],
)
def test_redact_email(email: str, expected: str) -> None:
    assert redact_email(email) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Jane Doe", "J. D."), ("janedoe", "j."), ("  Ana  ", "A."), ("", "")],
)
def test_redact_name(name: str, expected: str) -> None:
    assert redact_name(name) == expected


def test_redact_identity_merges_masked_names_and_keeps_stats() -> None:
    identity = Identity(
        email="jane@x.io",
        names={"Jane Doe": 2, "Janet Dunn": 1},
        roles={Role.AUTHOR},
        commits={"a", "b"},
    )
    redacted = redact_identity(identity)
    assert redacted.email == "j*****e@x.io"
    assert redacted.domain == "x.io"
    assert redacted.names == {"J. D.": 3}
    assert redacted.commit_count == 2
    assert identity.email == "jane@x.io"  # original untouched


def test_redact_groups_keeps_keys() -> None:
    (group,) = redact_groups([Group("x.io", [Identity(email="bob@x.io")])])
    assert group.key == "x.io"
    assert group.identities[0].email == "b*****b@x.io"
