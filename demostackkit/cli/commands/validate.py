"""demostackkit validate <industry> — validate industry config and fixtures."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

console = Console()


def validate(
    industry: Annotated[
        str | None, typer.Argument(help="Industry slug (omit to validate all)")
    ] = None,
) -> None:
    """Validate industry.yaml and fixture files for one or all industries."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root, skip_invalid=True)

    slugs = [industry] if industry else registry.slugs()
    if not slugs:
        console.print("[yellow]No industries to validate.[/yellow]")
        raise typer.Exit(1)

    errors_found = False
    for slug in slugs:
        console.print(f"\n[bold cyan]Validating '{slug}'...[/bold cyan]")

        if slug in registry.errors():
            console.print(f"  [red]✗ Config: {registry.errors()[slug]}[/red]")
            errors_found = True
            continue

        try:
            config = registry.get(slug)
        except Exception as exc:
            console.print(f"  [red]✗ Cannot load config: {exc}[/red]")
            errors_found = True
            continue

        # Validate referenced files exist
        industry_dir = config.industry_dir
        file_checks = [
            (industry_dir / config.data.items, "data.items"),
            (industry_dir / config.data.customers, "data.customers"),
            (industry_dir / config.data.suppliers, "data.suppliers"),
        ]
        for path, field_name in file_checks:
            if path.exists():
                console.print(f"  [green]✓ {field_name}[/green] ({path.name})")
            else:
                console.print(f"  [yellow]⚠ {field_name}[/yellow] not found: {path}")

        # Validate seeder modules can be imported
        from demostackkit.seeder.loader import discover_seeders

        try:
            seeder_classes = discover_seeders(industry_dir)
            console.print(f"  [green]✓ Seeders[/green] ({len(seeder_classes)} found)")
        except Exception as exc:
            console.print(f"  [red]✗ Seeder import error: {exc}[/red]")
            errors_found = True

        console.print("  [green]✓ Config schema[/green]")

    if errors_found:
        console.print("\n[bold red]Validation failed.[/bold red]")
        raise typer.Exit(1)
    else:
        console.print("\n[bold green]All validations passed.[/bold green]")
