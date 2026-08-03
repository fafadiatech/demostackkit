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

    console.print(f"[bold cyan]Starting '{config.name}' demo environment...[/bold cyan]")
    console.print(f"  Site: [bold]{config.site.name}[/bold]")
    console.print(f"  ERPNext: [bold]{config.erpnext_version}[/bold]")

    # Start shared infrastructure only (no profile).
    # The seeder containers in docker-compose.yml require a locally-built image
    # and are intended for direct `docker compose --profile <slug> up` usage.
    # The CLI handles seeding itself via `docker exec` (see _run_seed below).
    runner.up(profile=None, detach=detach)

    if detach and seed:
        console.print("\n[dim]Waiting for ERPNext to be ready before seeding...[/dim]")
        _wait_for_backend(runner, timeout_seconds=180)
        console.print(f"[bold cyan]Running seeders...[/bold cyan]")
        _run_seed(industry, repo_root)

    console.print(f"\n[bold green]Demo environment ready![/bold green]")
    console.print(f"  URL: [bold]http://{config.site.name}[/bold]")
    console.print(f"  Login: [bold]Administrator[/bold] / [bold]{config.site.admin_password}[/bold]")


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


def _run_seed(industry: str, repo_root: Path) -> None:
    """Invoke the seed command programmatically."""
    from demostackkit.cli.commands.seed import _do_seed
    _do_seed(industry, phase="all", repo_root=repo_root)
