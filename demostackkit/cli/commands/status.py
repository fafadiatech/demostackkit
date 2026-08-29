"""demostackkit status — show which industries are up and reachable."""

from __future__ import annotations

import subprocess

import requests
from rich.console import Console
from rich.table import Table

console = Console()

_BACKEND_CONTAINER = "demostackkit-backend-1"
_BENCH_PATH = "/home/frappe/frappe-bench"


def status() -> None:
    """Show shared infrastructure health and per-industry site status."""
    from demostackkit.cli.commands.up import _load_env_file
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root

    industries_root = get_industries_root()
    repo_root = industries_root.parent
    env_file = repo_root / "infra" / ".env"

    registry = IndustryRegistry.from_root(industries_root, skip_invalid=True)
    env_vars = _load_env_file(env_file)
    http_port = env_vars.get("HTTP_PORT", "80")

    infra_up, infra_detail = _check_infra()

    table = Table(title="demostackkit status", show_header=True, header_style="bold cyan")
    table.add_column("Slug", style="bold", min_width=14)
    table.add_column("Name")
    table.add_column("Status", justify="center")
    table.add_column("URL")

    if not infra_up:
        console.print(f"[red]Shared infrastructure is not healthy[/red] ({infra_detail}).")
        console.print("Run [bold]demostackkit up <industry>[/bold] to start it.\n")
        for cfg in registry.all():
            table.add_row(cfg.slug, cfg.name, "[dim]stopped[/dim]", "-")
        console.print(table)
        return

    for cfg in registry.all():
        site = cfg.site.name
        url = f"http://{site}" if http_port in ("80", "") else f"http://{site}:{http_port}"
        state = _site_state(site, url)
        table.add_row(cfg.slug, cfg.name, state, "-" if "not created" in state else url)

    console.print(table)
    console.print(f"[dim]Shared infrastructure: {infra_detail}[/dim]")


def _check_infra() -> tuple[bool, str]:
    """Return (healthy, detail) for the shared backend container."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Health.Status}}", _BACKEND_CONTAINER],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        return False, f"cannot query docker: {exc}"
    if result.returncode != 0:
        return False, "backend container not running"
    health = result.stdout.strip()
    return health == "healthy", f"backend {health}"


def _site_exists(site: str) -> bool:
    """Return True if the site has been created on the shared bench."""
    result = subprocess.run(
        [
            "docker",
            "exec",
            _BACKEND_CONTAINER,
            "test",
            "-f",
            f"{_BENCH_PATH}/sites/{site}/site_config.json",
        ],
        capture_output=True,
        timeout=10,
    )
    return result.returncode == 0


def _site_state(site: str, url: str) -> str:
    if not _site_exists(site):
        return "[dim]not created[/dim]"
    try:
        resp = requests.get(f"{url}/api/method/ping", timeout=3)
        if resp.ok:
            return "[green]running[/green]"
        return f"[yellow]unhealthy ({resp.status_code})[/yellow]"
    except requests.RequestException:
        return "[yellow]unreachable[/yellow]"
