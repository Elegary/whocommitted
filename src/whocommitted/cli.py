"""Command line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from whocommitted import __version__
from whocommitted.errors import WhocommittedError
from whocommitted.extractor import SortKey, extract, sort_identities
from whocommitted.filters import apply_filters, build_filters
from whocommitted.git import GitClient
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
        SortKey, typer.Option("--sort", "-s", case_sensitive=False, help="Sort order.")
    ] = SortKey.EMAIL,
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
    identities = sort_identities(apply_filters(identities, filters), sort)

    if output is None:
        render(identities, fmt, sys.stdout)
    else:
        with output.open("w", encoding="utf-8", newline="") as stream:
            render(identities, fmt, stream)
        err.print(f"[green]{len(identities)} email(s) written to {output}[/]", highlight=False)


@app.command("providers")
def providers_cmd() -> None:
    """List supported repository providers."""
    for provider in PROVIDERS:
        typer.echo(f"{provider.name:<10} {provider.description}")
