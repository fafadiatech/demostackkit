"""demostackkit restore <industry> — restore a site from backup."""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich.console import Console

console = Console()


def restore(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    backup_file: Annotated[
        str, typer.Argument(help="Path to .sql.gz backup file (inside container)")
    ],
) -> None:
    """Restore the industry site from a bench backup file."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.erpnext.bench import BenchClient

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    db_root_pw = os.environ.get("DB_ROOT_PASSWORD", "erpnext")

    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)
    console.print(f"[bold]Restoring {config.site.name} from {backup_file}...[/bold]")
    bench.restore(backup_file, db_root_password=db_root_pw)
    console.print("[green]Restore complete.[/green]")
