"""Core data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class RepoRef:
    """A repository resolved by a provider, ready to be cloned."""

    provider: str
    clone_url: str
    owner: str | None = None
    name: str | None = None
    web_url: str | None = None

    @property
    def display_name(self) -> str:
        if self.owner and self.name:
            return f"{self.owner}/{self.name}"
        return self.clone_url


class Role(StrEnum):
    AUTHOR = "author"
    COMMITTER = "committer"
    CO_AUTHOR = "co-author"


@dataclass(frozen=True, slots=True)
class Signature:
    """One identity occurrence in one commit."""

    name: str
    email: str
    role: Role
    date: datetime | None = None


@dataclass(frozen=True, slots=True)
class Commit:
    sha: str
    signatures: tuple[Signature, ...]


@dataclass(slots=True)
class Identity:
    """Aggregated view of every occurrence of one email address."""

    email: str
    names: dict[str, int] = field(default_factory=dict)
    roles: set[Role] = field(default_factory=set)
    commits: set[str] = field(default_factory=set)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @property
    def name(self) -> str:
        """Most frequently used name for this email."""
        if not self.names:
            return ""
        return max(self.names.items(), key=lambda item: (item[1], item[0]))[0]

    @property
    def domain(self) -> str:
        return self.email.rpartition("@")[2]

    @property
    def commit_count(self) -> int:
        return len(self.commits)

    def add(self, sha: str, signature: Signature) -> None:
        if signature.name:
            self.names[signature.name] = self.names.get(signature.name, 0) + 1
        self.roles.add(signature.role)
        self.commits.add(sha)
        if signature.date is not None:
            if self.first_seen is None or signature.date < self.first_seen:
                self.first_seen = signature.date
            if self.last_seen is None or signature.date > self.last_seen:
                self.last_seen = signature.date
