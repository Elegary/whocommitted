"""Provider registry.

Resolution order for a spec:

1. explicit prefix ``<provider>:<path>`` (e.g. ``github:owner/repo``);
2. URLs recognised by a hosted provider (``https://github.com/owner/repo``...);
3. ``owner/repo`` shorthand, resolved by the default provider;
4. any other git URL or local path (generic provider).

To support a new service, implement :class:`Provider` (usually by subclassing
:class:`HostedProvider`) and add an instance to ``PROVIDERS``.
"""

from __future__ import annotations

import re

from whocommitted.errors import InvalidRepoSpecError
from whocommitted.models import RepoRef
from whocommitted.providers.base import HostedProvider, Provider
from whocommitted.providers.generic import LOCAL_PREFIXES, GenericGitProvider
from whocommitted.providers.github import GitHubProvider

PROVIDERS: tuple[Provider, ...] = (GitHubProvider(), GenericGitProvider())
DEFAULT_PROVIDER = "github"

_SHORTHAND_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
_PREFIX_RE = re.compile(r"^(?P<name>[a-z][a-z0-9-]*):(?!//)(?P<path>.+)$")


def get_provider(name: str) -> Provider:
    for provider in PROVIDERS:
        if provider.name == name:
            return provider
    raise InvalidRepoSpecError(f"unknown provider: {name!r}")


def resolve(spec: str, default: str = DEFAULT_PROVIDER) -> RepoRef:
    """Resolve a user supplied repository spec into a :class:`RepoRef`."""
    spec = spec.strip()
    if not spec:
        raise InvalidRepoSpecError("empty repository spec")

    prefixed = _PREFIX_RE.match(spec)
    if prefixed and prefixed.group("name") in {p.name for p in PROVIDERS}:
        return get_provider(prefixed.group("name")).from_path(prefixed.group("path"))

    for provider in PROVIDERS:
        if isinstance(provider, HostedProvider):
            ref = provider.parse(spec)
            if ref is not None:
                return ref

    # ./repo and ../repo also look like owner/repo shorthand.
    if _SHORTHAND_RE.match(spec) and not spec.startswith(LOCAL_PREFIXES):
        return get_provider(default).from_path(spec)

    for provider in PROVIDERS:
        if not isinstance(provider, HostedProvider):
            ref = provider.parse(spec)
            if ref is not None:
                return ref

    raise InvalidRepoSpecError(
        f"cannot understand repository {spec!r}; use a URL or <owner>/<repo>"
    )


__all__ = [
    "DEFAULT_PROVIDER",
    "PROVIDERS",
    "GenericGitProvider",
    "GitHubProvider",
    "HostedProvider",
    "Provider",
    "get_provider",
    "resolve",
]
