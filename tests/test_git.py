from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.conftest import ALICE, BOB, CAROL, DAVE, RepoBuilder
from whocommitted.errors import GitCommandError, GitNotFoundError
from whocommitted.extractor import extract
from whocommitted.git import GitClient
from whocommitted.models import RepoRef, Role


def local_ref(path: Path) -> RepoRef:
    return RepoRef(provider="git", clone_url=path.as_uri())


def test_extract_sees_all_branches_tags_and_trailers(sample_repo: Path) -> None:
    by_email = {i.email: i for i in extract(local_ref(sample_repo))}
    assert set(by_email) == {
        ALICE[1],
        BOB[1],
        CAROL[1],
        DAVE[1],
        "49699333+dependabot[bot]@users.noreply.github.com",
        "noreply@github.com",
    }
    alice = by_email[ALICE[1]]
    assert alice.commit_count == 2
    assert alice.names == {"Alice": 2, "A. Liddell": 2}
    assert alice.first_seen is not None
    assert alice.first_seen.year == 2023
    assert by_email[BOB[1]].roles == {Role.CO_AUTHOR}
    assert by_email["noreply@github.com"].roles == {Role.COMMITTER}


def test_cloned_cleans_up(sample_repo: Path) -> None:
    client = GitClient()
    with client.cloned(sample_repo.as_uri()) as path:
        assert (path / "HEAD").exists()
    assert not path.exists()


def test_include_pulls_fetches_pull_refs(repo_builder: RepoBuilder) -> None:
    repo_builder.commit(ALICE)
    repo_builder.git("checkout", "-q", "-b", "pr")
    repo_builder.commit(("Forker", "forker@fork.dev"))
    sha = repo_builder.git("rev-parse", "HEAD").strip()
    repo_builder.git("checkout", "-q", "main")
    repo_builder.git("branch", "-q", "-D", "pr")
    repo_builder.git("update-ref", "refs/pull/1/head", sha)

    ref = local_ref(repo_builder.path)
    assert "forker@fork.dev" not in {i.email for i in extract(ref)}
    assert "forker@fork.dev" in {i.email for i in extract(ref, include_pulls=True)}


def test_clone_missing_repo(tmp_path: Path) -> None:
    with pytest.raises(GitCommandError, match="clone failed"):
        extract(local_ref(tmp_path / "missing"))


@pytest.mark.parametrize(
    "stderr",
    ["fatal: could not read Username for 'https://github.com'", "remote: Repository not found."],
)
def test_clone_auth_error_is_explained(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stderr: str
) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 128, "", stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(GitCommandError, match="not found or private"):
        GitClient().clone_bare("https://github.com/x/y.git", tmp_path / "d")


def test_clone_url_is_never_read_as_an_option(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    GitClient().clone_bare("--upload-pack=x", tmp_path / "d")
    args = calls[0]
    assert args.index("--") == args.index("--upload-pack=x") - 1


def test_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git", 1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(GitCommandError, match="timed out"):
        GitClient(timeout=1).run(["clone"])


def test_git_not_found() -> None:
    client = GitClient(executable="definitely-not-git")
    with pytest.raises(GitNotFoundError):
        client.run(["status"])
    with pytest.raises(GitNotFoundError):
        list(client.iter_log_records(Path()))


def test_log_failure(tmp_path: Path) -> None:
    with pytest.raises(GitCommandError, match="git log failed"):
        list(GitClient().iter_log_records(tmp_path))


def test_log_streams_across_chunks(repo_builder: RepoBuilder) -> None:
    long_name = "N" * 70000
    repo_builder.commit((long_name, "long@x.io"))
    repo_builder.commit(ALICE)
    emails = {i.email for i in extract(local_ref(repo_builder.path))}
    assert emails == {"long@x.io", ALICE[1]}
