"""GitHub provider."""

from __future__ import annotations

import re

from whocommitted.errors import InvalidRepoSpecError
from whocommitted.providers.base import HostedProvider

_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


class GitHubProvider(HostedProvider):
    name = "github"
    description = "github.com repositories (URL, SSH or owner/repo shorthand)"
    host = "github.com"

    def validate(self, owner: str, name: str) -> None:
        if not _OWNER_RE.match(owner):
            raise InvalidRepoSpecError(f"invalid GitHub owner: {owner!r}")
        if not _REPO_RE.match(name) or name in {".", ".."}:
            raise InvalidRepoSpecError(f"invalid GitHub repository name: {name!r}")
