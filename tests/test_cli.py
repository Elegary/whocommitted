from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from whocommitted import __version__
from whocommitted.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_providers() -> None:
    result = runner.invoke(app, ["providers"])
    assert result.exit_code == 0
    assert "github" in result.stdout


def test_extract_json_with_filters(sample_repo: Path) -> None:
    result = runner.invoke(
        app,
        ["extract", str(sample_repo), "-f", "json", "--no-bots", "--no-noreply", "-s", "commits"],
    )
    assert result.exit_code == 0, result.output
    emails = [row["email"] for row in json.loads(result.stdout)]
    assert emails[0] == "alice@example.com"
    assert sorted(emails) == [
        "alice@example.com",
        "bob@corp.io",
        "carol@feature.dev",
        "dave@tagged.org",
    ]


def test_extract_domain_to_file(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "emails.txt"
    result = runner.invoke(
        app, ["extract", str(sample_repo), "-f", "txt", "-d", "corp.io", "-o", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.read_text() == "bob@corp.io\tBob\n"
    assert "1 email(s) written" in result.stderr


def test_extract_table_default(sample_repo: Path) -> None:
    result = runner.invoke(app, ["extract", str(sample_repo)])
    assert result.exit_code == 0
    assert "6 email(s) found" in result.stdout


def test_invalid_spec_exit_code() -> None:
    result = runner.invoke(app, ["extract", "nope"])
    assert result.exit_code == 2
    assert "cannot understand" in result.stderr


def test_clone_error_exit_code(tmp_path: Path) -> None:
    result = runner.invoke(app, ["extract", str(tmp_path / "missing")])
    assert result.exit_code == 4
    assert "error" in result.stderr


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "extract" in result.output


def test_python_m_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "whocommitted", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert __version__ in result.stdout


def test_extract_group_by_domain_sorted_by_commits(sample_repo: Path) -> None:
    result = runner.invoke(
        app, ["extract", str(sample_repo), "-f", "json", "-g", "domain", "-s", "commits"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data[0]["group"] == "example.com"
    assert data[0]["commits"] == 2


def test_extract_multi_sort_reverse_txt(sample_repo: Path) -> None:
    result = runner.invoke(
        app,
        [
            "extract",
            str(sample_repo),
            "-f",
            "txt",
            "--no-noreply",
            "-s",
            "domain",
            "-s",
            "name",
            "-r",
        ],
    )
    assert result.exit_code == 0, result.output
    assert [line.split("\t")[0] for line in result.stdout.splitlines()] == [
        "dave@tagged.org",
        "carol@feature.dev",
        "alice@example.com",
        "bob@corp.io",
    ]
