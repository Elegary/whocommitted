from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

GIT_ENV_KEYS = (
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "GIT_COMMITTER_DATE",
)


class RepoBuilder:
    """Builds a throwaway git repository with controlled identities."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._counter = 0
        path.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        base = {k: v for k, v in os.environ.items() if k not in GIT_ENV_KEYS}
        base.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})
        return subprocess.run(
            ["git", *args],
            cwd=self.path,
            env={**base, **(env or {})},
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def commit(
        self,
        author: tuple[str, str],
        committer: tuple[str, str] | None = None,
        message: str = "change",
        date: str = "2024-01-01T12:00:00+00:00",
    ) -> None:
        self._counter += 1
        (self.path / f"file{self._counter}.txt").write_text(str(self._counter))
        self.git("add", ".")
        committer = committer or author
        self.git(
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            message,
            env={
                "GIT_AUTHOR_NAME": author[0],
                "GIT_AUTHOR_EMAIL": author[1],
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_NAME": committer[0],
                "GIT_COMMITTER_EMAIL": committer[1],
                "GIT_COMMITTER_DATE": date,
            },
        )


ALICE = ("Alice", "alice@example.com")
BOB = ("Bob", "bob@corp.io")
CAROL = ("Carol", "carol@feature.dev")
DAVE = ("Dave", "dave@tagged.org")
BOT = ("dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com")
GH = ("GitHub", "noreply@github.com")


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Repo whose identities are spread across branches, a tag and trailers.

    main:      alice (x2, one as "A. Liddell" with uppercased email), bot committed by GitHub
    feature:   carol, with Bob as co-author
    tag v-old: dave (on a branch that is deleted afterwards, only reachable via the tag)
    """
    repo = RepoBuilder(tmp_path / "src")
    repo.commit(ALICE, date="2023-01-01T10:00:00+00:00")
    repo.commit(("A. Liddell", "Alice@Example.com"), date="2024-06-01T10:00:00+00:00")
    repo.commit(BOT, committer=GH, message="bump deps")

    repo.git("checkout", "-q", "-b", "feature")
    repo.commit(CAROL, message=f"feat: thing\n\nCo-authored-by: {BOB[0]} <{BOB[1]}>\n")

    repo.git("checkout", "-q", "-b", "old", "main")
    repo.commit(DAVE)
    repo.git("tag", "v-old")
    repo.git("checkout", "-q", "main")
    repo.git("branch", "-q", "-D", "old")
    return repo.path


@pytest.fixture
def repo_builder(tmp_path: Path) -> RepoBuilder:
    return RepoBuilder(tmp_path / "custom")
