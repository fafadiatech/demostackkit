"""demostackkit up <industry> — start an industry demo environment."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from demostackkit.docker.compose_runner import ComposeRunner

import typer
from rich.console import Console

console = Console()


def up(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    detach: Annotated[
        bool, typer.Option("--detach/--no-detach", "-d", help="Run in background")
    ] = True,
    seed: Annotated[
        bool, typer.Option("--seed/--no-seed", help="Run seeders after startup")
    ] = True,
    currency: Annotated[
        str | None,
        typer.Option("--currency", help="Override currency ISO 4217 code, e.g. USD, INR"),
    ] = None,
) -> None:
    """Start the ERPNext demo environment for the given industry."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.docker.compose_builder import needs_generated_compose, write_generated_compose
    from demostackkit.docker.compose_runner import ComposeRunner

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)
    if currency:
        config.company.currency = currency

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
        from demostackkit.erpnext.bench import BenchClient

        bench = BenchClient(container="demostackkit-backend-1", site=config.site.name)
        apps_pruned = _reconcile_apps_txt(config, bench)
        apps_fetched = _fetch_extra_apps(config, bench)
        site_created = _create_site_if_needed(config, repo_root)
        _sync_extra_app_assets(config, bench, build=apps_fetched or site_created)
        if apps_pruned or apps_fetched or site_created:
            _reload_frappe_services(runner)
        console.print("[bold cyan]Running seeders...[/bold cyan]")
        _run_seed(industry, repo_root, currency=currency)

    console.print("\n[bold green]Demo environment ready![/bold green]")
    console.print(f"  URL: [bold]http://{config.site.name}[/bold]")
    console.print(
        f"  Login: [bold]Administrator[/bold] / [bold]{config.site.admin_password}[/bold]"
    )


# Frappe process containers that must reload after get-app / new-site / install-app.
# Frontend is restarted separately after backend is healthy so nginx re-resolves the
# backend upstream IP (otherwise jewellery.localhost can 502 after compose restart).
_FRAPPE_PROCESS_SERVICES = ("backend", "websocket", "queue-short", "queue-long", "scheduler")


def _reconcile_apps_txt(config: object, bench: object) -> bool:
    """Drop apps.txt entries whose app directory is no longer in the bench.

    sites/apps.txt lives in the persistent `sites` volume, but apps/ lives in the
    backend container's writable layer. Recreating that container (image bump,
    ERPNEXT_VERSION toggle, compose down/up) resets apps/ to the image's baked-in
    frappe + erpnext while apps.txt keeps every app a previous `bench get-app`
    added. Frappe imports each app named in apps.txt on any `bench --site` call, so
    a stale name raises ModuleNotFoundError long before seeding starts.

    Entries this industry declares in extra_apps are left in place — _fetch_extra_apps
    re-fetches them immediately after. Anything else is pruned; a later `up` for the
    industry that owns it re-adds it via bench get-app.

    Returns True if apps.txt was rewritten.
    """
    from demostackkit.core.config import IndustryConfig
    from demostackkit.erpnext.bench import BenchClient

    assert isinstance(config, IndustryConfig)
    assert isinstance(bench, BenchClient)

    listed = bench.apps_txt_entries()
    if not listed:
        return False

    will_refetch = {entry.name for entry in config.extra_apps}
    stale = [
        name for name in listed if name not in will_refetch and not bench.app_exists_in_bench(name)
    ]
    if not stale:
        return False

    console.print(f"[yellow]Pruning app(s) missing from the bench: {', '.join(stale)}[/yellow]")
    console.print(
        "[dim]Their apps/ directories are gone. Re-run `up` for an industry that "
        "declares them to restore them.[/dim]"
    )
    bench.write_apps_txt([name for name in listed if name not in stale])
    return True


def _sync_extra_app_assets(config: object, bench: object, *, build: bool) -> bool:
    """Build and materialize static assets for extra_apps so nginx can serve them.

    Returns True if assets were materialized into sites/assets/.
    """
    from demostackkit.core.config import IndustryConfig
    from demostackkit.erpnext.bench import BenchClient

    assert isinstance(config, IndustryConfig)
    assert isinstance(bench, BenchClient)

    app_names = [entry.name for entry in config.extra_apps]
    if not app_names:
        return False

    if build:
        console.print("[dim]Building assets for extra apps...[/dim]")
        bench.build_app_assets(app_names)

    console.print("[dim]Materializing extra app assets for frontend nginx...[/dim]")
    if bench.materialize_app_assets(app_names):
        console.print("[green]Extra app assets copied into sites/assets/.[/green]")
        return True

    console.print("[dim]Extra app assets already materialized.[/dim]")
    return False


def _fetch_extra_apps(config: object, bench: object) -> bool:
    """Fetch all extra_apps into the bench via bench get-app (before site creation).

    Returns True if any app was newly fetched.
    """
    from demostackkit.core.config import IndustryConfig
    from demostackkit.erpnext.bench import BenchClient

    assert isinstance(config, IndustryConfig)
    assert isinstance(bench, BenchClient)
    fetched = False
    for entry in config.extra_apps:
        if bench.app_exists_in_bench(entry.name):
            console.print(f"[dim]App '{entry.name}' already in bench, skipping get-app.[/dim]")
            continue
        console.print(
            f"[bold cyan]Fetching app '{entry.name}' (source={entry.source})...[/bold cyan]"
        )
        bench.get_app(entry)
        console.print(f"[green]App '{entry.name}' fetched.[/green]")
        fetched = True
    return fetched


def _wait_for_backend(runner: ComposeRunner, timeout_seconds: int = 180) -> None:
    """Poll until the backend service is healthy."""
    import subprocess

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format={{.State.Health.Status}}",
                    "demostackkit-backend-1",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout.strip() == "healthy":
                return
        except Exception:
            pass
        time.sleep(5)
    console.print(
        "[yellow]Warning: backend did not report healthy within timeout, proceeding anyway[/yellow]"
    )


def _reload_frappe_services(runner: ComposeRunner, timeout_seconds: int = 180) -> None:
    """Restart gunicorn/workers so newly created sites and apps are loaded."""
    console.print("[dim]Restarting backend to load new site/apps...[/dim]")
    runner.restart(*_FRAPPE_PROCESS_SERVICES)
    _wait_for_backend(runner, timeout_seconds=timeout_seconds)
    # Nginx resolves backend to an IP at start; refresh after backend is back.
    runner.restart("frontend")


def _create_site_if_needed(config: object, repo_root: Path) -> bool:
    """Create the Frappe site if it doesn't already exist, then install ERPNext.

    Returns True if the site was created (or recreated) in this run.
    """
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
        [
            "docker",
            "exec",
            "-e",
            "FRAPPE_STREAM_LOGGING=1",
            container,
            f"{bench_path}/env/bin/python",
            "-c",
            (
                "import frappe; "
                f"frappe.init(site='{site}', sites_path='{bench_path}/sites'); "
                "frappe.connect(); "
                "print('ready' if frappe.db.exists('Item Group', 'All Item Groups') else 'not_ready')"
            ),
        ],
        capture_output=True,
        text=True,
    )
    if setup_check.returncode == 0 and "ready" in setup_check.stdout:
        console.print(f"[dim]Site {site} already fully set up, skipping creation.[/dim]")
        return False

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
            [
                "docker",
                "exec",
                container,
                "bash",
                "-c",
                f"cd {bench_path} && bench --site {site} install-app {app_name}",
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(f"bench install-app {app_name} failed for {site}")

    console.print(f"[bold cyan]Running ERPNext setup wizard for {site}...[/bold cyan]")
    company = config.company
    # ERPNext's install_company() feeds fy_start_date/fy_end_date straight into a
    # Fiscal Year record. Omit them and getdate(None) resolves both to today, so
    # FiscalYear.validate_dates() throws InvalidDates and the site ends up with no
    # Fiscal Year at all. The shared Fiscal Years seeder fills in the remaining years.
    _, fy_start, fy_end = _current_fiscal_year(company.fiscal_year_start)
    # setup_complete(args) takes a single positional dict — use --args, not --kwargs.
    wizard_args = (
        f"[{{'language': 'English', 'country': '{company.country}', "
        f"'currency': '{company.currency}', 'timezone': '{config.site.timezone}', "
        f"'chart_of_accounts': 'Standard', "
        f"'fy_start_date': '{fy_start}', 'fy_end_date': '{fy_end}', "
        f"'company_name': '{company.name}', "
        f"'company_abbr': '{company.abbr}'}}]"
    )
    wizard_cmd = (
        f"cd {bench_path} && bench --site {site} execute "
        f"frappe.desk.page.setup_wizard.setup_wizard.setup_complete "
        f'--args "{wizard_args}"'
    )
    result = subprocess.run(["docker", "exec", container, "bash", "-c", wizard_cmd])
    if result.returncode != 0:
        raise RuntimeError(f"ERPNext setup wizard failed for {site}")
    return True


def _current_fiscal_year(fiscal_year_start: str) -> tuple[str, str, str]:
    """(year_label, start, end) ISO strings for the fiscal year containing today."""
    from datetime import date

    from demostackkit.seeder.utils import fiscal_year_windows

    today = date.today()
    label, start, end = fiscal_year_windows(fiscal_year_start, today, today)[0]
    return label, start.isoformat(), end.isoformat()


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


def _run_seed(industry: str, repo_root: Path, *, currency: str | None = None) -> None:
    """Invoke the seed command programmatically."""
    from demostackkit.cli.commands.seed import _do_seed

    _do_seed(industry, phase="all", repo_root=repo_root, currency=currency)
