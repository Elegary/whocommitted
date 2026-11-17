"""Predicates used to drop unwanted identities."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from whocommitted.models import Identity

IdentityFilter = Callable[[Identity], bool]
"""Return ``True`` to keep the identity."""

_BOT_LOCAL_RE = re.compile(r"(^|[-_.+])bot$")


def is_noreply(identity: Identity) -> bool:
    local, _, domain = identity.email.partition("@")
    return "noreply" in domain or local in {"noreply", "no-reply"}


def is_bot(identity: Identity) -> bool:
    if "[bot]" in identity.email or any("[bot]" in name for name in identity.names):
        return True
    local = identity.email.partition("@")[0]
    return bool(_BOT_LOCAL_RE.search(local))


def has_domain(identity: Identity, domains: Iterable[str]) -> bool:
    domain = identity.email.rpartition("@")[2]
    return any(domain == d or domain.endswith(f".{d}") for d in domains)


def build_filters(
    *, no_noreply: bool = False, no_bots: bool = False, domains: Iterable[str] = ()
) -> list[IdentityFilter]:
    filters: list[IdentityFilter] = []
    if no_noreply:
        filters.append(lambda i: not is_noreply(i))
    if no_bots:
        filters.append(lambda i: not is_bot(i))
    wanted = [d.lower().lstrip("@").strip() for d in domains if d.strip()]
    if wanted:
        filters.append(lambda i: has_domain(i, wanted))
    return filters


def apply_filters(
    identities: Iterable[Identity], filters: Iterable[IdentityFilter]
) -> list[Identity]:
    active = list(filters)
    return [i for i in identities if all(f(i) for f in active)]
