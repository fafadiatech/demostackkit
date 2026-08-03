"""demostackkit create <industry> — create and initialise the Frappe site."""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich.console import Console

console = Console()


def create(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
) -> None:
    """Create the Frappe site for the given industry (without seeding)."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.erpnext.bench import BenchClient

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    db_root_pw = os.environ.get("DB_ROOT_PASSWORD", "erpnext")
    admin_pw = os.environ.get("SITE_ADMIN_PASSWORD", "admin")

    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)

    console.print(f"[bold]Creating site {config.site.name}...[/bold]")
    bench.new_site(
        admin_password=admin_pw,
        db_root_password=db_root_pw,
        install_apps=[a for a in config.required_apps if a != "frappe"],
    )
    console.print(f"[green]Site created: http://{config.site.name}[/green]")
    console.print(f"Run [bold]demostackkit seed {industry}[/bold] to load demo data.")
