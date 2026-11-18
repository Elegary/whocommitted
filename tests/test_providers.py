from __future__ import annotations

from pathlib import Path

import pytest

from whocommitted.errors import InvalidRepoSpecError
from whocommitted.models import RepoRef
from whocommitted.providers import PROVIDERS, get_provider, resolve


@pytest.mark.parametrize(
    "spec",
    [
        "octocat/Hello-World",
        "  octocat/Hello-World  ",
        "github:octocat/Hello-World",
        "https://github.com/octocat/Hello-World",
        "https://github.com/octocat/Hello-World/",
        "https://github.com/octocat/Hello-World.git",
        "https://www.github.com/octocat/Hello-World",
        "http://github.com/octocat/Hello-World",
        "HTTPS://GitHub.com/octocat/Hello-World",
        "github.com/octocat/Hello-World",
        "https://github.com/octocat/Hello-World/tree/main/src",
        "https://github.com/octocat/Hello-World/commit/abc123",
        "https://github.com/octocat/Hello-World?tab=readme#top",
        "git@github.com:octocat/Hello-World.git",
        "ssh://git@github.com/octocat/Hello-World.git",
        "ssh://git@github.com:22/octocat/Hello-World",
    ],
)
def test_github_specs(spec: str) -> None:
    assert resolve(spec) == RepoRef(
        provider="github",
        owner="octocat",
        name="Hello-World",
        clone_url="https://github.com/octocat/Hello-World.git",
        web_url="https://github.com/octocat/Hello-World",
    )


def test_repo_name_with_dots() -> None:
    ref = resolve("owner/my.repo.js")
    assert ref.name == "my.repo.js"
    assert ref.display_name == "owner/my.repo.js"


@pytest.mark.parametrize(
    "spec",
    [
        "",
        "   ",
        "octocat",
        "https://github.com/octocat",
        "https://github.com/-bad-/repo",
        "github:inv@lid/repo",
        "owner/..",
        "not a repo at all",
        "unknown:owner/repo",
    ],
)
def test_invalid_specs(spec: str) -> None:
    with pytest.raises(InvalidRepoSpecError):
        resolve(spec)


@pytest.mark.parametrize(
    "spec",
    [
        "https://gitlab.com/group/sub/project.git",
        "ssh://git@example.org/repo.git",
        "git@gitlab.com:group/project.git",
        "file:///srv/git/repo.git",
        "git://example.org/repo.git",
    ],
)
def test_generic_urls_are_passed_through(spec: str) -> None:
    ref = resolve(spec)
    assert ref.provider == "git"
    assert ref.clone_url == spec
    assert ref.display_name == spec


def test_local_path(tmp_path: Path) -> None:
    ref = resolve(str(tmp_path))
    assert ref.provider == "git"
    assert ref.clone_url == tmp_path.resolve().as_uri()


@pytest.mark.parametrize("prefix", ["./", "../"])
def test_relative_local_path_is_not_shorthand(
    prefix: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "sub").mkdir()
    monkeypatch.chdir(tmp_path / "sub")
    ref = resolve(f"{prefix}repo")
    assert ref.provider == "git"
    assert ref.clone_url == (tmp_path / "sub" / prefix / "repo").resolve().as_uri()


def test_git_prefix() -> None:
    assert resolve("git:https://example.org/r.git").clone_url == "https://example.org/r.git"
    assert resolve("git:anything").clone_url == "anything"


def test_registry() -> None:
    assert [p.name for p in PROVIDERS] == ["github", "git"]
    assert get_provider("github").name == "github"
    with pytest.raises(InvalidRepoSpecError):
        get_provider("nope")


def test_generic_provider_has_no_default_shorthand() -> None:
    with pytest.raises(InvalidRepoSpecError):
        resolve("owner/repo", default="nope")
