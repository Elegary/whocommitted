"""Command line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from whocommitted import __version__
from whocommitted.errors import WhocommittedError
from whocommitted.extractor import extract
from whocommitted.filters import apply_filters, build_filters
from whocommitted.git import GitClient
from whocommitted.ordering import GroupBy, SortKey, group_identities, sort_identities
from whocommitted.output import OutputFormat, render
from whocommitted.providers import PROVIDERS, resolve

app = typer.Typer(
    help="Extract every email address that committed to a git repository.",
    no_args_is_help=True,
    add_completion=False,
)
err = Console(stderr=True)


def _version(value: bool) -> None:
    if value:
        typer.echo(f"whocommitted {__version__}")
        raise typer.Exit


@app.callback()
def main(
    _version_flag: Annotated[
        bool,
        typer.Option("--version", callback=_version, is_eager=True, help="Show version and exit."),
    ] = False,
) -> None:
    """whocommitted - committer email extractor."""


@app.command("extract")
def extract_cmd(
    repo: Annotated[
        str,
        typer.Argument(
            help="Repository: owner/repo, https://github.com/owner/repo, any git URL or path."
        ),
    ],
    fmt: Annotated[
        OutputFormat, typer.Option("--format", "-f", case_sensitive=False, help="Output format.")
    ] = OutputFormat.TABLE,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", dir_okay=False, writable=True, help="Write to file."),
    ] = None,
    sort: Annotated[
        list[SortKey] | None,
        typer.Option(
            "--sort",
            "-s",
            case_sensitive=False,
            help="Sort key, repeatable (first = primary). "
            "commits/last-seen sort descending, others ascending. [default: email]",
        ),
    ] = None,
    reverse: Annotated[
        bool, typer.Option("--reverse", "-r", help="Reverse the sort order.")
    ] = False,
    group_by: Annotated[
        GroupBy,
        typer.Option(
            "--group-by",
            "-g",
            case_sensitive=False,
            help="Group results by email domain or kind (bot, noreply, personal, organization).",
        ),
    ] = GroupBy.NONE,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            min=1,
            help="Keep only the first N emails (after filtering and sorting).",
        ),
    ] = None,
    include_pulls: Annotated[
        bool,
        typer.Option("--include-pulls", help="Also scan pull request heads (GitHub refs/pull/*)."),
    ] = False,
    no_noreply: Annotated[
        bool, typer.Option("--no-noreply", help="Drop noreply addresses.")
    ] = False,
    no_bots: Annotated[bool, typer.Option("--no-bots", help="Drop bot accounts.")] = False,
    domains: Annotated[
        list[str] | None,
        typer.Option("--domain", "-d", help="Keep only this email domain (repeatable)."),
    ] = None,
    timeout: Annotated[
        float, typer.Option(help="Timeout in seconds for each git command.", min=1)
    ] = 600,
) -> None:
    """Extract author, committer and co-author emails from every branch and tag."""
    try:
        ref = resolve(repo)
        with err.status(f"Cloning {ref.display_name} (metadata only)..."):
            identities = extract(ref, GitClient(timeout=timeout), include_pulls=include_pulls)
    except WhocommittedError as exc:
        err.print(f"[bold red]error:[/] {exc}", highlight=False)
        raise typer.Exit(exc.exit_code) from exc

    filters = build_filters(no_noreply=no_noreply, no_bots=no_bots, domains=domains or ())
    keys = sort or [SortKey.EMAIL]
    identities = sort_identities(apply_filters(identities, filters), keys, reverse=reverse)
    if limit is not None:
        identities = identities[:limit]
    groups = group_identities(identities, group_by, keys, reverse=reverse)

    if output is None:
        render(groups, fmt, sys.stdout)
    else:
        with output.open("w", encoding="utf-8", newline="") as stream:
            render(groups, fmt, stream)
        err.print(f"[green]{len(identities)} email(s) written to {output}[/]", highlight=False)


@app.command("providers")
def providers_cmd() -> None:
    """List supported repository providers."""
    for provider in PROVIDERS:
        typer.echo(f"{provider.name:<10} {provider.description}")
