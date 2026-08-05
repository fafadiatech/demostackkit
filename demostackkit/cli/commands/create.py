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
    from demostackkit.cli.commands.up import _reload_frappe_services
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.docker.compose_runner import ComposeRunner
    from demostackkit.erpnext.bench import BenchClient

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    db_root_pw = os.environ.get("DB_ROOT_PASSWORD", "erpnext")
    admin_pw = os.environ.get("SITE_ADMIN_PASSWORD", "admin")

    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)

    for entry in config.extra_apps:
        if bench.app_exists_in_bench(entry.name):
            console.print(f"[dim]App '{entry.name}' already in bench, skipping get-app.[/dim]")
            continue
        console.print(f"[bold]Fetching app '{entry.name}' (source={entry.source})...[/bold]")
        bench.get_app(entry)

    console.print(f"[bold]Creating site {config.site.name}...[/bold]")
    bench.new_site(
        admin_password=admin_pw,
        db_root_password=db_root_pw,
        install_apps=[a for a in config.required_apps if a != "frappe"]
        + [e.name for e in config.extra_apps],
    )

    repo_root = industries_root.parent
    runner = ComposeRunner(
        compose_file=repo_root / "infra" / "docker-compose.yml",
        env_file=repo_root / "infra" / ".env",
    )
    _reload_frappe_services(runner)

    console.print(f"[green]Site created: http://{config.site.name}[/green]")
    console.print(f"Run [bold]demostackkit seed {industry}[/bold] to load demo data.")
