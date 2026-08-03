"""demostackkit list — show all discovered industries."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
import typer

console = Console()


def list_industries() -> None:
    """List all available industry demo environments."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root, skip_invalid=True)

    if not len(registry):
        console.print("[yellow]No industries found.[/yellow]")
        console.print(f"Expected industry directories under: [bold]{industries_root}[/bold]")
        raise typer.Exit(1)

    table = Table(title=f"Available Industries ({len(registry)} found)", show_header=True, header_style="bold cyan")
    table.add_column("Slug", style="bold", min_width=16)
    table.add_column("Name")
    table.add_column("Version", justify="center")
    table.add_column("Site")
    table.add_column("Currency", justify="center")
    table.add_column("ERPNext", justify="center")

    for cfg in registry.all():
        table.add_row(
            cfg.slug,
            cfg.name,
            cfg.version,
            cfg.site.name,
            cfg.company.currency,
            cfg.erpnext_version,
        )

    console.print(table)

    if registry.errors():
        console.print("\n[bold red]Invalid industries (skipped):[/bold red]")
        for slug, err in registry.errors().items():
            console.print(f"  [red]{slug}[/red]: {err}")
