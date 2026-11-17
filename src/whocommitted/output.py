"""Output formatters."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, TextIO

from rich.console import Console
from rich.table import Table

from whocommitted.models import Identity, Role

Formatter = Callable[[Sequence[Identity], TextIO], None]

_ROLE_ORDER = list(Role)


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    TXT = "txt"


def _roles(identity: Identity) -> list[str]:
    return [role.value for role in _ROLE_ORDER if role in identity.roles]


def to_dict(identity: Identity) -> dict[str, Any]:
    return {
        "email": identity.email,
        "name": identity.name,
        "names": sorted(identity.names),
        "roles": _roles(identity),
        "commits": identity.commit_count,
        "first_seen": identity.first_seen.isoformat() if identity.first_seen else None,
        "last_seen": identity.last_seen.isoformat() if identity.last_seen else None,
    }


def write_json(identities: Sequence[Identity], stream: TextIO) -> None:
    json.dump([to_dict(i) for i in identities], stream, indent=2, ensure_ascii=False)
    stream.write("\n")


CSV_COLUMNS = ("email", "name", "names", "roles", "commits", "first_seen", "last_seen")


def write_csv(identities: Sequence[Identity], stream: TextIO) -> None:
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for identity in identities:
        row = to_dict(identity)
        row["names"] = "; ".join(row["names"])
        row["roles"] = "; ".join(row["roles"])
        writer.writerow(row)


def write_txt(identities: Sequence[Identity], stream: TextIO) -> None:
    for identity in identities:
        stream.write(f"{identity.email}\t{identity.name}\n")


def write_table(identities: Sequence[Identity], stream: TextIO) -> None:
    table = Table(title=f"{len(identities)} email(s) found", title_justify="left")
    table.add_column("Email", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Roles", style="magenta")
    table.add_column("Commits", justify="right", style="green", no_wrap=True)
    table.add_column("Last seen", style="dim", no_wrap=True)
    for identity in identities:
        table.add_row(
            identity.email,
            ", ".join(sorted(identity.names, key=lambda n: -identity.names[n])),
            ", ".join(_roles(identity)),
            str(identity.commit_count),
            identity.last_seen.date().isoformat() if identity.last_seen else "",
        )
    Console(file=stream, soft_wrap=False).print(table)


FORMATTERS: dict[OutputFormat, Formatter] = {
    OutputFormat.TABLE: write_table,
    OutputFormat.JSON: write_json,
    OutputFormat.CSV: write_csv,
    OutputFormat.TXT: write_txt,
}


def render(identities: Sequence[Identity], fmt: OutputFormat, stream: TextIO) -> None:
    FORMATTERS[fmt](identities, stream)
