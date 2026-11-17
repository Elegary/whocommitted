"""Thin wrapper around the ``git`` executable."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from whocommitted.errors import GitCommandError, GitNotFoundError

FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"
TRAILER_SEP = "\x1d"

LOG_FIELDS = ("%H", "%an", "%ae", "%aI", "%cn", "%ce", "%cI")
LOG_FORMAT = (
    "%x1f".join(LOG_FIELDS) + "%x1f%(trailers:key=Co-authored-by,valueonly,separator=%x1d)%x1e"
)

PULL_REFSPEC = "+refs/pull/*/head:refs/pull/*/head"

_AUTH_HINTS = ("could not read Username", "Authentication failed", "Repository not found")


class GitClient:
    """Runs git commands non-interactively."""

    def __init__(self, executable: str = "git", timeout: float | None = 600) -> None:
        self.executable = executable
        self.timeout = timeout

    @property
    def env(self) -> dict[str, str]:
        # Never block on a credential prompt: GitHub answers 401 for missing repos.
        return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "LC_ALL": "C"}

    def ensure_available(self) -> None:
        if shutil.which(self.executable) is None:
            raise GitNotFoundError(f"{self.executable!r} executable not found in PATH")

    def run(self, args: Sequence[str], cwd: Path | None = None) -> str:
        self.ensure_available()
        try:
            result = subprocess.run(  # noqa: S603 - arguments are never passed to a shell
                [self.executable, *args],
                cwd=cwd,
                env=self.env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitCommandError(f"git {args[0]} timed out after {self.timeout}s") from exc
        if result.returncode != 0:
            message = result.stderr.strip() or f"exit code {result.returncode}"
            raise GitCommandError(f"git {args[0]} failed: {message}")
        return result.stdout

    def clone_bare(self, url: str, dest: Path) -> None:
        """Clone every branch and tag without downloading file contents."""
        try:
            self.run(["clone", "--bare", "--quiet", "--filter=blob:none", url, str(dest)])
        except GitCommandError as exc:
            if any(hint in str(exc) for hint in _AUTH_HINTS):
                raise GitCommandError(
                    f"repository {url} not found or private (authentication required)"
                ) from exc
            raise

    def fetch_pulls(self, repo: Path) -> None:
        """Fetch pull request heads (GitHub ``refs/pull/*``), including fork commits."""
        self.run(["fetch", "--quiet", "origin", PULL_REFSPEC], cwd=repo)

    def iter_log_records(self, repo: Path) -> Iterator[str]:
        """Stream raw log records of every commit reachable from any ref."""
        self.ensure_available()
        args = [
            self.executable,
            "-c",
            "log.showSignature=false",
            "log",
            "--all",
            "--encoding=UTF-8",
            f"--format={LOG_FORMAT}",
        ]
        with subprocess.Popen(  # noqa: S603
            args,
            cwd=repo,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        ) as process:
            assert process.stdout is not None  # noqa: S101 - guaranteed by PIPE
            buffer = ""
            while chunk := process.stdout.read(65536):
                buffer += chunk
                *records, buffer = buffer.split(RECORD_SEP)
                for record in records:
                    if record.strip():
                        yield record
            if buffer.strip():
                yield buffer
            stderr = process.stderr.read() if process.stderr else ""
            if process.wait() != 0:
                raise GitCommandError(f"git log failed: {stderr.strip()}")

    @contextmanager
    def cloned(self, url: str, *, include_pulls: bool = False) -> Iterator[Path]:
        """Clone ``url`` into a temporary directory removed on exit."""
        with tempfile.TemporaryDirectory(prefix="whocommitted-") as tmp:
            dest = Path(tmp) / "repo.git"
            self.clone_bare(url, dest)
            if include_pulls:
                self.fetch_pulls(dest)
            yield dest
