"""demostackkit backup <industry> — backup the industry site."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

console = Console()


def backup(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
) -> None:
    """Create a bench backup of the industry site."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.erpnext.bench import BenchClient

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    repo_root = industries_root.parent
    backup_dir = str(repo_root / "infra" / "backups")

    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)
    console.print(f"[bold]Backing up {config.site.name}...[/bold]")
    output = bench.backup(backup_dir)
    console.print(f"[green]Backup complete.[/green]\n{output}")
