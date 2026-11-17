"""Output formatters.

Every formatter receives a list of :class:`Group`. Ungrouped output is a single
group whose ``key`` is ``None`` and is rendered flat.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, TextIO

from rich.console import Console
from rich.table import Table
from rich.text import Text

from whocommitted.models import Identity, Role
from whocommitted.ordering import Group

Formatter = Callable[[Sequence[Group], TextIO], None]

_ROLE_ORDER = list(Role)


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    TXT = "txt"


def _is_grouped(groups: Sequence[Group]) -> bool:
    return any(group.key is not None for group in groups)


def _roles(identity: Identity) -> list[str]:
    return [role.value for role in _ROLE_ORDER if role in identity.roles]


def _summary(group: Group) -> str:
    return f"{len(group.identities)} email(s), {group.commit_count} commit(s)"


def to_dict(identity: Identity) -> dict[str, Any]:
    return {
        "email": identity.email,
        "name": identity.name,
        "names": sorted(identity.names),
        "domain": identity.domain,
        "roles": _roles(identity),
        "commits": identity.commit_count,
        "first_seen": identity.first_seen.isoformat() if identity.first_seen else None,
        "last_seen": identity.last_seen.isoformat() if identity.last_seen else None,
    }


def write_json(groups: Sequence[Group], stream: TextIO) -> None:
    data: list[dict[str, Any]]
    if _is_grouped(groups):
        data = [
            {
                "group": group.key,
                "emails": len(group.identities),
                "commits": group.commit_count,
                "identities": [to_dict(i) for i in group.identities],
            }
            for group in groups
        ]
    else:
        data = [to_dict(i) for group in groups for i in group.identities]
    json.dump(data, stream, indent=2, ensure_ascii=False)
    stream.write("\n")


CSV_COLUMNS = (
    "email",
    "name",
    "names",
    "domain",
    "roles",
    "commits",
    "first_seen",
    "last_seen",
)


def write_csv(groups: Sequence[Group], stream: TextIO) -> None:
    grouped = _is_grouped(groups)
    columns = ("group", *CSV_COLUMNS) if grouped else CSV_COLUMNS
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for group in groups:
        for identity in group.identities:
            row = to_dict(identity)
            row["names"] = "; ".join(row["names"])
            row["roles"] = "; ".join(row["roles"])
            if grouped:
                row["group"] = group.key
            writer.writerow(row)


def write_txt(groups: Sequence[Group], stream: TextIO) -> None:
    grouped = _is_grouped(groups)
    for index, group in enumerate(groups):
        if grouped:
            if index:
                stream.write("\n")
            stream.write(f"# {group.key} ({_summary(group)})\n")
        for identity in group.identities:
            stream.write(f"{identity.email}\t{identity.name}\n")


def _name_cell(identity: Identity) -> Text:
    """Main name, plus the number of other spellings used with this email."""
    cell = Text(identity.name)
    if len(identity.names) > 1:
        cell.append(f" (+{len(identity.names) - 1})", style="dim")
    return cell


def _table(group: Group, title: Text) -> Table:
    table = Table(title=title, title_justify="left")
    table.add_column("Email", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Roles", style="magenta")
    table.add_column("Commits", justify="right", style="green", no_wrap=True)
    table.add_column("Last seen", style="dim", no_wrap=True)
    for identity in group.identities:
        # Text instances are never parsed as markup: "dependabot[bot]" must stay intact.
        table.add_row(
            Text(identity.email),
            _name_cell(identity),
            ", ".join(_roles(identity)),
            str(identity.commit_count),
            identity.last_seen.date().isoformat() if identity.last_seen else "",
        )
    return table


def write_table(groups: Sequence[Group], stream: TextIO) -> None:
    console = Console(file=stream, soft_wrap=False)
    total = sum(len(g.identities) for g in groups)
    if not _is_grouped(groups):
        console.print(_table(groups[0], Text(f"{total} email(s) found")))
        return
    console.print(f"[bold]{total} email(s) in {len(groups)} group(s)[/]")
    for group in groups:
        console.print()
        title = Text.assemble((group.key or "", "bold"), f" - {_summary(group)}")
        console.print(_table(group, title))


FORMATTERS: dict[OutputFormat, Formatter] = {
    OutputFormat.TABLE: write_table,
    OutputFormat.JSON: write_json,
    OutputFormat.CSV: write_csv,
    OutputFormat.TXT: write_txt,
}


def render(groups: Sequence[Group], fmt: OutputFormat, stream: TextIO) -> None:
    FORMATTERS[fmt](groups, stream)
