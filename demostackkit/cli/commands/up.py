"""demostackkit up <industry> — start an industry demo environment."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console()


def up(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    detach: Annotated[bool, typer.Option("--detach/--no-detach", "-d", help="Run in background")] = True,
    seed: Annotated[bool, typer.Option("--seed/--no-seed", help="Run seeders after startup")] = True,
) -> None:
    """Start the ERPNext demo environment for the given industry."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.docker.compose_runner import ComposeRunner
    from demostackkit.docker.compose_builder import needs_generated_compose, write_generated_compose

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    repo_root = industries_root.parent
    compose_file = repo_root / "infra" / "docker-compose.yml"
    env_file = repo_root / "infra" / ".env"
    generated_dir = repo_root / "infra" / ".generated"

    extra_files: list[Path] = []
    if needs_generated_compose(industry):
        generated = write_generated_compose(config, industries_root, generated_dir)
        extra_files.append(generated)
        console.print(f"[dim]Generated compose override: {generated}[/dim]")

    runner = ComposeRunner(
        compose_file=compose_file,
        env_file=env_file,
        extra_compose_files=extra_files,
    )

    env_vars = _load_env_file(env_file)
    active_version = env_vars.get("ERPNEXT_VERSION", "v15")

    console.print(f"[bold cyan]Starting '{config.name}' demo environment...[/bold cyan]")
    console.print(f"  Site: [bold]{config.site.name}[/bold]")
    console.print(f"  ERPNext: [bold]{active_version}[/bold]")

    # Start shared infrastructure only (no profile).
    # The seeder containers in docker-compose.yml require a locally-built image
    # and are intended for direct `docker compose --profile <slug> up` usage.
    # The CLI handles seeding itself via `docker exec` (see _run_seed below).
    runner.up(profile=None, detach=detach)

    if detach and seed:
        console.print("\n[dim]Waiting for ERPNext to be ready before seeding...[/dim]")
        _wait_for_backend(runner, timeout_seconds=180)
        if config.extra_apps:
            from demostackkit.erpnext.bench import BenchClient
            bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)
            _fetch_extra_apps(config, bench)
        _create_site_if_needed(config, repo_root)
        console.print(f"[bold cyan]Running seeders...[/bold cyan]")
        _run_seed(industry, repo_root)

    console.print(f"\n[bold green]Demo environment ready![/bold green]")
    console.print(f"  URL: [bold]http://{config.site.name}[/bold]")
    console.print(f"  Login: [bold]Administrator[/bold] / [bold]{config.site.admin_password}[/bold]")


def _fetch_extra_apps(config: "object", bench: "object") -> None:
    """Fetch all extra_apps into the bench via bench get-app (before site creation)."""
    from demostackkit.core.config import IndustryConfig
    from demostackkit.erpnext.bench import BenchClient
    assert isinstance(config, IndustryConfig)
    assert isinstance(bench, BenchClient)
    for entry in config.extra_apps:
        if bench.app_exists_in_bench(entry.name):
            console.print(f"[dim]App '{entry.name}' already in bench, skipping get-app.[/dim]")
            continue
        console.print(f"[bold cyan]Fetching app '{entry.name}' (source={entry.source})...[/bold cyan]")
        bench.get_app(entry)
        console.print(f"[green]App '{entry.name}' fetched.[/green]")


def _wait_for_backend(runner: "ComposeRunner", timeout_seconds: int = 180) -> None:
    """Poll until the backend service is healthy."""
    import subprocess
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Health.Status}}", "demostackkit-backend-1"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip() == "healthy":
                return
        except Exception:
            pass
        time.sleep(5)
    console.print("[yellow]Warning: backend did not report healthy within timeout, proceeding anyway[/yellow]")


def _create_site_if_needed(config: "object", repo_root: Path) -> None:
    """Create the Frappe site if it doesn't already exist, then install ERPNext."""
    import subprocess
    from demostackkit.core.config import IndustryConfig

    assert isinstance(config, IndustryConfig)
    site = config.site.name
    container = "demostackkit-backend-1"
    bench_path = "/home/frappe/frappe-bench"

    env_vars = _load_env_file(repo_root / "infra" / ".env")
    db_root_password = env_vars.get("DB_ROOT_PASSWORD", "erpnext")
    admin_password = env_vars.get("SITE_ADMIN_PASSWORD", "admin")

    # Check if site is fully set up by querying the DB for "All Item Groups",
    # which the ERPNext setup wizard creates. We can't rely on apps.txt (Frappe v15
    # tracks installs in the DB) or site_config.json (created before install-app runs).
    setup_check = subprocess.run(
        ["docker", "exec", "-e", "FRAPPE_STREAM_LOGGING=1", container,
         f"{bench_path}/env/bin/python", "-c",
         (
             "import frappe; "
             f"frappe.init(site='{site}', sites_path='{bench_path}/sites'); "
             "frappe.connect(); "
             "print('ready' if frappe.db.exists('Item Group', 'All Item Groups') else 'not_ready')"
         )],
        capture_output=True,
        text=True,
    )
    if setup_check.returncode == 0 and "ready" in setup_check.stdout:
        console.print(f"[dim]Site {site} already fully set up, skipping creation.[/dim]")
        return

    # Drop any partial site (site_config.json exists but setup is incomplete).
    drop_check = subprocess.run(
        ["docker", "exec", container, "test", "-f", f"{bench_path}/sites/{site}/site_config.json"],
        capture_output=True,
    )
    if drop_check.returncode == 0:
        console.print(f"[dim]Dropping incomplete site {site}...[/dim]")
        drop_cmd = (
            f"cd {bench_path} && bench drop-site {site} "
            f"--mariadb-root-password '{db_root_password}' --force"
        )
        subprocess.run(["docker", "exec", container, "bash", "-c", drop_cmd])

    console.print(f"[bold cyan]Creating site {site}...[/bold cyan]")
    create_cmd = (
        f"cd {bench_path} && "
        f"bench new-site {site} "
        f"--mariadb-root-password '{db_root_password}' "
        f"--admin-password '{admin_password}' "
        "--no-mariadb-socket"
    )
    result = subprocess.run(["docker", "exec", container, "bash", "-c", create_cmd])
    if result.returncode != 0:
        raise RuntimeError(f"bench new-site failed for {site}")

    apps_to_install = [a for a in config.required_apps if a != "frappe"]
    apps_to_install += [e.name for e in config.extra_apps]
    for app_name in apps_to_install:
        console.print(f"[bold cyan]Installing {app_name} on {site}...[/bold cyan]")
        result = subprocess.run(
            ["docker", "exec", container, "bash", "-c",
             f"cd {bench_path} && bench --site {site} install-app {app_name}"]
        )
        if result.returncode != 0:
            raise RuntimeError(f"bench install-app {app_name} failed for {site}")

    console.print(f"[bold cyan]Running ERPNext setup wizard for {site}...[/bold cyan]")
    company = config.company
    # setup_complete(args) takes a single positional dict — use --args, not --kwargs.
    wizard_args = (
        f"[{{'language': 'English', 'country': '{company.country}', "
        f"'currency': '{company.currency}', 'timezone': 'Asia/Kolkata', "
        f"'chart_of_accounts': 'Standard'}}]"
    )
    wizard_cmd = (
        f"cd {bench_path} && bench --site {site} execute "
        f"frappe.desk.page.setup_wizard.setup_wizard.setup_complete "
        f"--args \"{wizard_args}\""
    )
    result = subprocess.run(["docker", "exec", container, "bash", "-c", wizard_cmd])
    if result.returncode != 0:
        raise RuntimeError(f"ERPNext setup wizard failed for {site}")


def _load_env_file(env_file: Path) -> dict:
    """Parse a simple key=value .env file, ignoring comments and blank lines."""
    env_vars: dict = {}
    if not env_file.exists():
        return env_vars
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()
    return env_vars


def _run_seed(industry: str, repo_root: Path) -> None:
    """Invoke the seed command programmatically."""
    from demostackkit.cli.commands.seed import _do_seed
    _do_seed(industry, phase="all", repo_root=repo_root)
