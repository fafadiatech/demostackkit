"""demostackkit install-app <industry> <app> — fetch and install a Frappe app on demand."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

console = Console()


def install_app(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    app: Annotated[str, typer.Argument(help="App name, e.g. hrms")],
    source: Annotated[str, typer.Option("--source", help="frappe | github | local")] = "frappe",
    url: Annotated[
        str | None, typer.Option("--url", help="GitHub URL (required when --source github)")
    ] = None,
    branch: Annotated[str | None, typer.Option("--branch", help="Git branch (optional)")] = None,
    path: Annotated[
        str | None,
        typer.Option("--path", help="Host directory path (required when --source local)"),
    ] = None,
) -> None:
    """Fetch and install a Frappe app into a running industry stack.

    Does not modify industry.yaml — use extra_apps in YAML for permanent configuration.

    Examples:

      # From frappe.io
      demostackkit install-app garment hrms
      demostackkit install-app garment hrms --branch version-15

      # From GitHub
      demostackkit install-app garment hrms --source github --url https://github.com/frappe/hrms

      # From a local directory on this machine
      demostackkit install-app garment my_app --source local --path /Users/me/projects/my_app
    """
    from demostackkit.cli.commands.up import _reload_frappe_services
    from demostackkit.core.config import AppEntry
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.docker.compose_runner import ComposeRunner
    from demostackkit.erpnext.bench import BenchClient

    # Construct AppEntry — reuses all Pydantic validation (missing url, missing path, etc.)
    try:
        entry = AppEntry(name=app, source=source, url=url, branch=branch, host_path=path)
    except Exception as exc:
        console.print(f"[red]Invalid options: {exc}[/red]")
        raise typer.Exit(code=1)

    industries_root = get_industries_root()
    config = IndustryRegistry.from_root(industries_root).get(industry)
    bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)

    if bench.app_exists_in_bench(app):
        console.print(
            f"[dim]App '{app}' already in bench — skipping get-app, running install-app only.[/dim]"
        )
    else:
        console.print(f"[bold cyan]Fetching '{app}' (source={source})...[/bold cyan]")
        bench.get_app(entry)
        console.print(f"[green]App '{app}' fetched.[/green]")

    console.print(f"[bold cyan]Installing '{app}' on {config.site.name}...[/bold cyan]")
    bench.install_app(app)

    console.print("[dim]Building and materializing app assets for frontend nginx...[/dim]")
    bench.build_app_assets([app])
    bench.materialize_app_assets([app])

    repo_root = industries_root.parent
    runner = ComposeRunner(
        compose_file=repo_root / "infra" / "docker-compose.yml",
        env_file=repo_root / "infra" / ".env",
    )
    _reload_frappe_services(runner)

    console.print(f"[bold green]Done. '{app}' installed on {config.site.name}.[/bold green]")
