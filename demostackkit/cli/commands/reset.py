"""demostackkit reset <industry> — drop, recreate, and reseed an industry site."""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich.console import Console

console = Console()


def reset(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
) -> None:
    """
    Completely reset the demo environment.

    Drops the Frappe site, recreates it, installs apps, and reruns all seeders.
    The result is guaranteed to be identical to a fresh installation.
    """
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.erpnext.bench import BenchClient

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    if not yes:
        confirm = typer.confirm(
            f"This will DESTROY all data for '{industry}' ({config.site.name}) and rebuild from scratch. Continue?",
            default=False,
        )
        if not confirm:
            raise typer.Abort()

    db_root_pw = os.environ.get("DB_ROOT_PASSWORD", "erpnext")

    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)

    # 1. Drop site
    console.print(f"[bold red]Dropping site {config.site.name}...[/bold red]")
    try:
        bench.drop_site(db_root_password=db_root_pw)
    except Exception as exc:
        console.print(f"[yellow]Could not drop site (may not exist): {exc}[/yellow]")

    # 2. Fetch extra apps (bench get-app) before creating site
    for entry in config.extra_apps:
        if bench.app_exists_in_bench(entry.name):
            console.print(f"[dim]App '{entry.name}' already in bench, skipping get-app.[/dim]")
            continue
        console.print(f"[bold]Fetching app '{entry.name}' (source={entry.source})...[/bold]")
        bench.get_app(entry)

    # 3. Create site, install apps, and run the ERPNext setup wizard — reuses
    # the same helper `up` uses so a reset produces a site that is set up
    # identically (fiscal year, company, chart of accounts) rather than just
    # a bare site with no root docs (Item Group, Customer Group, etc).
    from demostackkit.cli.commands.up import _create_site_if_needed

    console.print(f"[bold]Creating site {config.site.name}...[/bold]")
    _create_site_if_needed(config, industries_root.parent)

    # 4. Reseed
    console.print("[bold cyan]Running seeders...[/bold cyan]")
    from demostackkit.cli.commands.seed import _do_seed

    _do_seed(industry, phase="all", repo_root=industries_root.parent)

    console.print("\n[bold green]Reset complete![/bold green]")
    console.print(f"  URL: http://{config.site.name}")
