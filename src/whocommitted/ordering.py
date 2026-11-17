"""Sorting and grouping of identities for presentation."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from whocommitted.filters import classify
from whocommitted.models import Identity


class SortKey(StrEnum):
    EMAIL = "email"
    NAME = "name"
    DOMAIN = "domain"
    COMMITS = "commits"
    FIRST_SEEN = "first-seen"
    LAST_SEEN = "last-seen"


class GroupBy(StrEnum):
    NONE = "none"
    DOMAIN = "domain"
    KIND = "kind"


def _timestamp(value: datetime | None, missing: float) -> float:
    return value.timestamp() if value is not None else missing


# (key function, natural order is descending). Missing dates always sort last.
_SORTERS: dict[SortKey, tuple[Callable[[Identity], object], bool]] = {
    SortKey.EMAIL: (lambda i: i.email, False),
    SortKey.NAME: (lambda i: i.name.casefold(), False),
    SortKey.DOMAIN: (lambda i: i.domain, False),
    SortKey.COMMITS: (lambda i: i.commit_count, True),
    SortKey.FIRST_SEEN: (lambda i: _timestamp(i.first_seen, math.inf), False),
    SortKey.LAST_SEEN: (lambda i: _timestamp(i.last_seen, -math.inf), True),
}

ALPHABETICAL_KEYS = frozenset({SortKey.EMAIL, SortKey.NAME, SortKey.DOMAIN})


def sort_identities(
    identities: Iterable[Identity], keys: Sequence[SortKey] = (), *, reverse: bool = False
) -> list[Identity]:
    """Sort by several keys, the first one being the primary key.

    Each key has a natural direction (commits and last-seen: highest/most recent
    first, others ascending); ``reverse`` flips all of them. Email is the final
    tie-breaker so the output is deterministic.
    """
    result = sorted(identities, key=lambda i: i.email, reverse=reverse)
    for key in reversed(keys):
        func, descending = _SORTERS[key]
        result.sort(key=func, reverse=descending != reverse)  # type: ignore[arg-type]
    return result


@dataclass(frozen=True, slots=True)
class Group:
    """A labelled slice of identities; ``key`` is ``None`` when output is not grouped."""

    key: str | None
    identities: list[Identity]

    @property
    def commit_count(self) -> int:
        return len(set().union(*(i.commits for i in self.identities)))


_GROUPERS: dict[GroupBy, Callable[[Identity], str]] = {
    GroupBy.DOMAIN: lambda i: i.domain,
    GroupBy.KIND: lambda i: classify(i).value,
}


def group_identities(
    identities: Sequence[Identity],
    group_by: GroupBy,
    keys: Sequence[SortKey] = (),
    *,
    reverse: bool = False,
) -> list[Group]:
    """Split already sorted identities into groups, keeping their order inside each group.

    Groups are ordered alphabetically when the primary sort key is alphabetical
    (email, name, domain) and by total commits otherwise.
    """
    if group_by is GroupBy.NONE:
        return [Group(None, list(identities))]

    buckets: dict[str, list[Identity]] = {}
    for identity in identities:
        buckets.setdefault(_GROUPERS[group_by](identity), []).append(identity)
    groups = [Group(key, members) for key, members in buckets.items()]

    groups.sort(key=lambda g: g.key or "", reverse=reverse)
    if keys and keys[0] not in ALPHABETICAL_KEYS:
        groups.sort(key=lambda g: (g.commit_count, len(g.identities)), reverse=not reverse)
    return groups
