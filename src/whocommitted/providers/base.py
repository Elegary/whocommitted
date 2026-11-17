"""Provider abstraction: turn a user supplied spec into a cloneable :class:`RepoRef`."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import ClassVar

from whocommitted.errors import InvalidRepoSpecError
from whocommitted.models import RepoRef


class Provider(ABC):
    """Knows how to recognise and resolve repositories of one hosting service."""

    name: ClassVar[str]
    description: ClassVar[str]

    @abstractmethod
    def parse(self, spec: str) -> RepoRef | None:
        """Return a :class:`RepoRef` if ``spec`` belongs to this provider, ``None`` otherwise.

        Raise :class:`InvalidRepoSpecError` when the spec clearly targets this provider
        but is malformed.
        """

    def from_path(self, path: str) -> RepoRef:
        """Resolve a bare ``owner/repo`` style path (shorthand or ``name:path`` prefix)."""
        raise InvalidRepoSpecError(f"provider {self.name!r} does not support shorthand specs")


class HostedProvider(Provider):
    """Base class for services hosting repositories under ``https://<host>/<path>``.

    Subclasses only need to set ``host`` and, if needed, override :meth:`split_path`
    (e.g. GitLab supports nested groups).
    """

    host: ClassVar[str]

    def _url_patterns(self) -> tuple[re.Pattern[str], ...]:
        host = re.escape(self.host)
        return (
            re.compile(rf"^(?:https?://)?(?:www\.)?{host}/(?P<path>.+)$", re.IGNORECASE),
            re.compile(rf"^ssh://git@{host}(?::\d+)?/(?P<path>.+)$", re.IGNORECASE),
            re.compile(rf"^git@{host}:(?P<path>.+)$", re.IGNORECASE),
        )

    def parse(self, spec: str) -> RepoRef | None:
        for pattern in self._url_patterns():
            match = pattern.match(spec)
            if match:
                return self.from_path(match.group("path"))
        return None

    def from_path(self, path: str) -> RepoRef:
        path = path.split("?", 1)[0].split("#", 1)[0]
        segments = [segment for segment in path.split("/") if segment]
        owner, name = self.split_path(segments)
        name = name.removesuffix(".git")
        self.validate(owner, name)
        return RepoRef(
            provider=self.name,
            owner=owner,
            name=name,
            clone_url=self.clone_url(owner, name),
            web_url=f"https://{self.host}/{owner}/{name}",
        )

    def split_path(self, segments: list[str]) -> tuple[str, str]:
        """Split URL path segments into ``(owner, name)``; extra segments are ignored."""
        if len(segments) < 2:
            raise InvalidRepoSpecError(
                f"expected <owner>/<repo> for {self.host}, got {'/'.join(segments)!r}"
            )
        return segments[0], segments[1]

    def validate(self, owner: str, name: str) -> None:
        """Hook for provider specific naming rules."""

    def clone_url(self, owner: str, name: str) -> str:
        return f"https://{self.host}/{owner}/{name}.git"
