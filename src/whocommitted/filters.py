"""Predicates used to drop unwanted identities."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from enum import StrEnum

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
    domain = identity.domain
    return any(domain == d or domain.endswith(f".{d}") for d in domains)


PERSONAL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "msn.com",
        "yahoo.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "aol.com",
        "proton.me",
        "protonmail.com",
        "pm.me",
        "gmx.com",
        "gmx.de",
        "gmx.net",
        "web.de",
        "mail.ru",
        "yandex.ru",
        "yandex.com",
        "qq.com",
        "163.com",
        "126.com",
        "fastmail.com",
        "hey.com",
        "zoho.com",
        "tutanota.com",
        "free.fr",
        "orange.fr",
        "laposte.net",
        "wp.pl",
        "o2.pl",
        "interia.pl",
    }
)


class Kind(StrEnum):
    BOT = "bot"
    NOREPLY = "noreply"
    PERSONAL = "personal"
    ORGANIZATION = "organization"


def classify(identity: Identity) -> Kind:
    """Coarse category of an address: bot, noreply, webmail or own domain."""
    if is_bot(identity):
        return Kind.BOT
    if is_noreply(identity):
        return Kind.NOREPLY
    if identity.domain in PERSONAL_DOMAINS:
        return Kind.PERSONAL
    return Kind.ORGANIZATION


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
