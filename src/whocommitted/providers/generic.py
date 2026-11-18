"""Fallback provider accepting any URL or local path git can clone."""

from __future__ import annotations

import re
from pathlib import Path

from whocommitted.errors import InvalidRepoSpecError
from whocommitted.models import RepoRef
from whocommitted.providers.base import Provider

_URL_RE = re.compile(r"^(?:https?|ssh|git|file)://\S+$", re.IGNORECASE)
_SCP_RE = re.compile(r"^[\w.-]+@[\w.-]+:\S+$")
LOCAL_PREFIXES = ("/", "./", "../", "~")


class GenericGitProvider(Provider):
    name = "git"
    description = "any git URL (https, ssh, git, file) or local path"

    def parse(self, spec: str) -> RepoRef | None:
        if _URL_RE.match(spec) or _SCP_RE.match(spec):
            return RepoRef(provider=self.name, clone_url=spec)
        if spec.startswith(LOCAL_PREFIXES):
            path = Path(spec).expanduser().resolve()
            return RepoRef(provider=self.name, clone_url=path.as_uri())
        return None

    def from_path(self, path: str) -> RepoRef:
        if path.startswith("-"):
            # Would be read by git as an option (e.g. --upload-pack=<command>).
            raise InvalidRepoSpecError(f"invalid repository {path!r}")
        ref = self.parse(path)
        if ref is None:
            ref = RepoRef(provider=self.name, clone_url=path)
        return ref
