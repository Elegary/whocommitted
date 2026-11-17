"""Parse git log output and aggregate identities by email."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

from whocommitted.git import FIELD_SEP, LOG_FIELDS, TRAILER_SEP, GitClient
from whocommitted.models import Commit, Identity, RepoRef, Role, Signature

_TRAILER_RE = re.compile(r"^\s*(?P<name>.*?)\s*<(?P<email>[^<>]*)>\s*$")
_EXPECTED_FIELDS = len(LOG_FIELDS) + 1


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def parse_trailer(value: str) -> tuple[str, str] | None:
    """Parse a ``Name <email>`` trailer value."""
    match = _TRAILER_RE.match(value)
    if not match or not match.group("email").strip():
        return None
    return match.group("name"), match.group("email").strip()


def parse_record(record: str) -> Commit | None:
    """Parse one record produced with :data:`whocommitted.git.LOG_FORMAT`."""
    fields = record.lstrip("\n").split(FIELD_SEP)
    if len(fields) < _EXPECTED_FIELDS:
        return None
    sha, a_name, a_email, a_date, c_name, c_email, c_date = fields[: len(LOG_FIELDS)]
    trailers = FIELD_SEP.join(fields[len(LOG_FIELDS) :])

    author_date = _parse_date(a_date)
    signatures = [
        Signature(a_name, a_email, Role.AUTHOR, author_date),
        Signature(c_name, c_email, Role.COMMITTER, _parse_date(c_date)),
    ]
    for raw in trailers.split(TRAILER_SEP):
        parsed = parse_trailer(raw)
        if parsed:
            signatures.append(Signature(parsed[0], parsed[1], Role.CO_AUTHOR, author_date))
    return Commit(sha=sha.strip(), signatures=tuple(signatures))


def aggregate(commits: Iterable[Commit]) -> list[Identity]:
    """Group signatures by case-insensitive email address."""
    identities: dict[str, Identity] = {}
    for commit in commits:
        for signature in commit.signatures:
            email = signature.email.strip()
            if not email:
                continue
            key = email.lower()
            identity = identities.get(key)
            if identity is None:
                identity = identities[key] = Identity(email=key)
            identity.add(commit.sha, signature)
    return list(identities.values())


def extract(
    repo: RepoRef, client: GitClient | None = None, *, include_pulls: bool = False
) -> list[Identity]:
    """Clone ``repo`` and return every identity found in its history (all refs)."""
    client = client or GitClient()
    with client.cloned(repo.clone_url, include_pulls=include_pulls) as path:
        commits = (c for r in client.iter_log_records(path) if (c := parse_record(r)))
        return aggregate(commits)
