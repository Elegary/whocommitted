"""Mask personal data so results can be shared or shown publicly."""

from __future__ import annotations

from dataclasses import replace

from whocommitted.models import Identity
from whocommitted.ordering import Group

MASK = "*****"


def redact_email(email: str) -> str:
    """``dana.lane@example.com`` -> ``d*****e@example.com``; the domain is kept."""
    local, at, domain = email.rpartition("@")
    if not at:
        local, domain = email, ""
    masked = local[:1] + MASK if len(local) <= 2 else local[0] + MASK + local[-1]
    return f"{masked}{at}{domain}"


def redact_name(name: str) -> str:
    """``Dana Lane`` -> ``D. L.``"""
    return " ".join(f"{word[0]}." for word in name.split())


def redact_identity(identity: Identity) -> Identity:
    names: dict[str, int] = {}
    for name, count in identity.names.items():
        masked = redact_name(name)
        names[masked] = names.get(masked, 0) + count
    return replace(identity, email=redact_email(identity.email), names=names)


def redact_groups(groups: list[Group]) -> list[Group]:
    return [replace(g, identities=[redact_identity(i) for i in g.identities]) for g in groups]
